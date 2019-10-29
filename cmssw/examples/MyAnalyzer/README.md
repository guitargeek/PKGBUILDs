# Example CMSSW analyzer

This is a little example on how to use the CMSSW framework on Arch Linux. It is a little different compared to what we
are used to because we got to use cmake instead of scram, but it is not much more complicated, just a bit different.

Let's try to stick to the package structure that we know from CMSSW, which entails a `plugins` directory for the plugin
sources and a `python` directory for configuration files. First, we can put the code of our simple analyzer that prints out the
transverse momentum and pseudorapidities of all electrons into [plugins/MyAnalyzer.cc](plugins/MyAnalyzer.cc). Second,
we can write a little python config file into [python/MyAnalyzer_cfg.py](python/MyAnalyzer_cfg.py). It should just take
a random MiniAOD file as a source, feel free to change it but remember you can't use the grid here.

So far everything was pretty ordinary, but the [CMakeLists.txt](CMakeLists.txt) file that replaces the `BuildFile.xml`
from scram looks a bit different. Some comments are added to that file itself, please check it out.

You can now build the plugin and run the configuration as follows (starting from this directory):

```bash
mkdir build
cd build
cmake ..
make
edmPluginRefresh .
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD
cd ..
cmsRun python/MyAnalyzer_cfg.py
```

It is a bit annoying because we had to manually refresh the plugins and add the build directory to the `LD_LIBRARY_PATH`
such that cmsRun finds the plugins. Now we can appreciate how nicely scram is organizing everything else for us in the
bakground and that we don't have to do this manually.

Anyway, you should now get the expected and familiar CMSSW output!
