import FWCore.ParameterSet.Config as cms

process = cms.Process("MyAnalyzer")

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
        "file:/home/jonas/PhD/022E2036-A2D9-E711-9A8C-0CC47A13D2A4.root"
    )
)

process.analyzer = cms.EDAnalyzer('MyAnalyzer')

process.p = cms.Path(process.analyzer)
