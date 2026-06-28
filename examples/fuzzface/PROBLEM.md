---
title: Fuzz Face
domain: audio
tier: T1
---

Reproduce the classic **Fuzz Face** guitar fuzz pedal — a famously minimal
two-transistor design that still defines the sound of '60s fuzz.

The Fuzz Face is a direct-coupled, two-stage transistor amplifier with strong DC
feedback from the second stage's collector back to the first stage's base. That
feedback both biases the circuit (the output should sit near mid-supply for
symmetric headroom) and, under signal, drives both transistors hard into
clipping — producing the thick, compressed, harmonically rich fuzz tone. It runs
from a 9 V rail. Classic silicon versions use NPN transistors (e.g. BC108);
germanium versions are PNP.

Design target: a 9 V, NPN-silicon Fuzz Face that, driven by a representative
~50 mV / 1 kHz guitar signal, biases for headroom, delivers high gain, and
clips hard into heavy harmonic distortion. The measurable acceptance criteria
are in `spec.md`.

Reference (for the librarian to consult): the Fuz Central Fuzz Face page,
<https://fuzzcentral.ssguitar.com/fuzzface.php>, plus ElectroSmash's Fuzz Face
circuit analysis for component values and bias points.

This is the harness's **go-to test**: `/target` is not needed — seed it with
`make seed-fuzzface`, then run `/solve` and watch schema-forge design and tune
the circuit on http://127.0.0.1:8000.
