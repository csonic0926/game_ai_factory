# Adapters

## Purpose

Adapters, if added, should consume stable outputs from the core workflow.

## Stable inputs for adapters

- `manifest.json`
- atlas PNG when produced
- reference-pair `validation.json`
- generated tile PNGs

## Rule

Adapters should not redefine the meaning of the core Blender reference workflow.
They should only translate already-generated outputs into downstream engine formats.
