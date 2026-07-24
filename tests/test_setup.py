import importlib.util
import os
import tempfile
import unittest

SETUP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "setup.py")
spec = importlib.util.spec_from_file_location("factory_setup", SETUP_PATH)
factory_setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(factory_setup)


def make_factory(root, skills=("game-story-factory",)):
    for name in skills:
        skill_dir = os.path.join(root, "story", "skills", name)
        os.makedirs(skill_dir, exist_ok=True)
        with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as handle:
            handle.write("# %s\n" % name)
    return root


class DiscoverSkillsTest(unittest.TestCase):
    def test_finds_nested_skill_dirs(self):
        with tempfile.TemporaryDirectory() as root:
            make_factory(root, ("alpha", "beta"))
            names = [name for name, _ in factory_setup.discover_skills(root)]
            self.assertEqual(names, ["alpha", "beta"])

    def test_ignores_dirs_without_skill_md(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "story", "skills", "empty"))
            self.assertEqual(factory_setup.discover_skills(root), [])


class SyncSkillsTest(unittest.TestCase):
    def test_creates_symlink_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            target = os.path.join(root, "skills")
            os.makedirs(target)
            factory_setup.sync_skills(factory, [target])
            dest = os.path.join(target, "game-story-factory")
            self.assertTrue(os.path.islink(dest))
            report = factory_setup.sync_skills(factory, [target])
            self.assertTrue(any(line.startswith("ok ") for line in report))

    def test_never_touches_foreign_entries(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            target = os.path.join(root, "skills")
            foreign = os.path.join(target, "game-story-factory")
            os.makedirs(foreign)
            marker = os.path.join(foreign, "user_owned.txt")
            with open(marker, "w", encoding="utf-8") as handle:
                handle.write("mine\n")
            report = factory_setup.sync_skills(factory, [target])
            self.assertTrue(any("CONFLICT" in line for line in report))
            self.assertTrue(os.path.isfile(marker))

    def test_removes_stale_factory_links(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"), ("alpha", "beta"))
            target = os.path.join(root, "skills")
            os.makedirs(target)
            factory_setup.sync_skills(factory, [target])
            import shutil
            shutil.rmtree(os.path.join(factory, "story", "skills", "beta"))
            factory_setup.sync_skills(factory, [target])
            self.assertFalse(os.path.lexists(os.path.join(target, "beta")))
            self.assertTrue(os.path.islink(os.path.join(target, "alpha")))

    def test_dedupes_targets_resolving_to_same_dir(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            target = os.path.join(root, "skills")
            os.makedirs(target)
            alias = os.path.join(root, "skills_alias")
            os.symlink(target, alias)
            report = factory_setup.sync_skills(factory, [target, alias])
            self.assertTrue(any("same directory" in line for line in report))

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            target = os.path.join(root, "skills")
            os.makedirs(target)
            factory_setup.sync_skills(factory, [target], dry_run=True)
            self.assertEqual(os.listdir(target), [])


class MarkedBlockTest(unittest.TestCase):
    def test_insert_then_replace_without_duplication(self):
        block = factory_setup.render_routing_block()
        text = factory_setup.upsert_marked_block("# Existing rules\n", block)
        self.assertEqual(text.count(factory_setup.BLOCK_BEGIN), 1)
        self.assertIn("# Existing rules", text)
        again = factory_setup.upsert_marked_block(text, block)
        self.assertEqual(again.count(factory_setup.BLOCK_BEGIN), 1)
        self.assertEqual(again.count(factory_setup.BLOCK_END), 1)

    def test_replacement_preserves_text_after_block(self):
        block = factory_setup.render_routing_block()
        text = factory_setup.upsert_marked_block("intro\n", block) + "\n## Tail section\n"
        replaced = factory_setup.upsert_marked_block(text, block)
        self.assertIn("## Tail section", replaced)


class LinkGameRepoTest(unittest.TestCase):
    def test_link_writes_all_surfaces_idempotently(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            game = os.path.join(root, "game")
            os.makedirs(game)
            with open(os.path.join(game, "AGENTS.md"), "w", encoding="utf-8") as handle:
                handle.write("# Game rules\n")
            factory_setup.link_game_repo(factory, game)
            pointer = os.path.join(game, "design", "AI_FACTORY.local.md")
            self.assertTrue(os.path.isfile(pointer))
            with open(pointer, encoding="utf-8") as handle:
                self.assertIn(factory, handle.read())
            with open(os.path.join(game, ".gitignore"), encoding="utf-8") as handle:
                self.assertIn("design/AI_FACTORY.local.md", handle.read())
            self.assertTrue(os.path.isfile(os.path.join(game, "CLAUDE.md")))
            factory_setup.link_game_repo(factory, game)
            with open(os.path.join(game, "AGENTS.md"), encoding="utf-8") as handle:
                body = handle.read()
            self.assertEqual(body.count(factory_setup.BLOCK_BEGIN), 1)
            self.assertIn("# Game rules", body)

    def test_existing_claude_md_is_untouched(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            game = os.path.join(root, "game")
            os.makedirs(game)
            with open(os.path.join(game, "CLAUDE.md"), "w", encoding="utf-8") as handle:
                handle.write("user content\n")
            factory_setup.link_game_repo(factory, game)
            with open(os.path.join(game, "CLAUDE.md"), encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "user content\n")

    def test_refuses_factory_as_game_repo(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            with self.assertRaises(SystemExit):
                factory_setup.link_game_repo(factory, os.path.join(factory, "story"))

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            factory = make_factory(os.path.join(root, "factory"))
            game = os.path.join(root, "game")
            os.makedirs(game)
            factory_setup.link_game_repo(factory, game, dry_run=True)
            self.assertFalse(os.path.exists(os.path.join(game, "design")))
            self.assertFalse(os.path.exists(os.path.join(game, "CLAUDE.md")))


if __name__ == "__main__":
    unittest.main()
