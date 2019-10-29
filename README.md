# PKGBUILDs
My custom packages for Arch Linux.

## CMSSW related packages

Once I tried to build CMSSW on my laptop, therefore we have here many packages which are either dependencies of CMSSW of
represent CMSSW itself:

* [classlib](classlib)
* [cmssw](cmssw)
* [coral](coral)
* [dd4hep](dd4hep)
* [heppdt](heppdt)
* [libcms-md5](libcms-md5)
* [lwtnn](lwtnn)

### Note on the CMSSW package

The idea was to have a python script that converts the `BuildFile.xml` files for scram to `CMakeLists.txt` files.
Unfortunately, not the whole CMSSW is contained in this package (because it would take way to long to compile), but just
the **FWCore** and **DataFormats** subsystems. This is already pretty cool: you can now open CMS AOD and MiniAOD files
on your laptop and read all the objects, and you can write a little test analyzier to check if the framework works in
general, which you can find in the [examples directory](cmssw/examples).

This is actually all the functionality I want from CMSSW on my laptop, so I won't work on this much anymore. Probably I
will just streamline the currently very messy cmake conversion script at some point when I have time but that's about it.
However, you are interested in making the cmssw package for Arch Linux more complete, I would be happy to work with you!


## Other general CMS packages

Nicely safe-contained, there is a package for the [HiggsAnalysis-CombinedLimit](https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit) tool:

* [higgs-combine](higgs-combine)

## Personal analysis related packages

A few packages are probably not of interest to anyone, because I use them for my personal physics analysis. These
packages are:

* [aminnj-pyfiles](aminnj-pyfiles)
* [python-plottery](python-plottery)
* [rooutil](rooutil)

## Other packages

Some packages don't fall in any of the previous categories:

* [fastforest](fastforest)
* [onnxruntime](onnxruntime)
