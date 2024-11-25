# kaisha-island-rs

This is a dummy project of mine (@yuqingsh) with Tongji University.

I intended to get my hands dirty with some raw and real data before I start my phd thesis.
The project uses real Sentinel-2 RGB image and study the land cover classification.

## Requirement

Ubuntu==20.04

Python==3.10

torch==2.5.1

## Research Outline

The util.py file provides a automated download method from Sentinel Hub. For each month, a mosaicked image with least CC is downloaded.
