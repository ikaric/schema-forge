---
title: Diode Clipping Overdrive Stage
domain: audio
tier: T2
---

Design the nonlinear clipping stage at the heart of a guitar **overdrive** pedal.

A hot pickup signal (~0.7 V peak at 1 kHz) must be **symmetrically soft-clipped**
by anti-parallel diodes so the stage adds musical harmonic distortion, then
coupled to the output through a high-pass "tone" stage that sets where the low
end rolls off. The clamp level is set by the diode forward drop; the series
resistor sets how hard the signal is driven into the diodes.

This is a worked example used to prove the harness end to end: it converges
easily, exhibits real nonlinearity (clipping + THD), and has an assertable
small-signal corner. The concrete, machine-checkable targets live in `spec.md`.
