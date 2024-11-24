# kaisha-island-rs

This is a dummy project of mine (@yuqingsh) with Tongji University.

I intended to get my hands dirty with some raw and real data before I start my phd project.
The project's aim is to discover the relation between the extension of Shanghai City and the change of
vegetation cover area through high-resolution satellite image.

## Requirement

Ubuntu==20.04

Python==3.10

torch==2.5.1

## Research Outline

Since we are talking about the realationship between the extension of city and
vegetation cover area, we need a time series of data. The time interval I chose
is from Jan 1 2010 to Dec 31 2023. For each months, we download the

## Data Download

Now I have my AOI (aera of interest) decided, I need to download data for analysis. I chose Sentinel-2,
since it doesn't require any application for usage and has mature API for automated workflow.
