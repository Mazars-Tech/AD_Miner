## [1.6.1](https://github.com/Mazars-Tech/AD_Miner/compare/v1.6.0...v1.6.1) (2024-10-03)


### Bug Fixes

* better requests and anomaly_acl bug ([ebd6749](https://github.com/Mazars-Tech/AD_Miner/commit/ebd674917b7496a035779148921c104a0e649f23))
* only first letter was used to generate acl anomaly name label instances ([9089968](https://github.com/Mazars-Tech/AD_Miner/commit/908996843a77672d8689c7ebf1efec87b2888ecb))



# [1.6.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.5.2...v1.6.0) (2024-09-10)


### Bug Fixes

* add missing requests in config.json ([#168](https://github.com/Mazars-Tech/AD_Miner/issues/168)) ([5afe7db](https://github.com/Mazars-Tech/AD_Miner/commit/5afe7db6f633a121b0d2f9f53c59bac04018dfe9))
* fix crash when a computer is member of DA ([9416e78](https://github.com/Mazars-Tech/AD_Miner/commit/9416e78093990102391d17231b16dc01b66c0efe))


### Features

* add cache files warning (chores) ([1ced00e](https://github.com/Mazars-Tech/AD_Miner/commit/1ced00ec8a8d64ef310502acf9c05acb33c3faef))



## [1.5.2](https://github.com/Mazars-Tech/AD_Miner/compare/v1.5.1...v1.5.2) (2024-07-25)


### Bug Fixes

* fix deadlock issue ([6017b2b](https://github.com/Mazars-Tech/AD_Miner/commit/6017b2b0d576de9b1c94d1bde400cd7fdeb63293))



## [1.5.1](https://github.com/Mazars-Tech/AD_Miner/compare/v1.5.0...v1.5.1) (2024-07-24)


### Bug Fixes

* add EDCS edges and fix not displayed graphs bug ([d17b843](https://github.com/Mazars-Tech/AD_Miner/commit/d17b843388535439a77db024f6c7527c806794fd))
* remove MSOL from path candidates ([8451485](https://github.com/Mazars-Tech/AD_Miner/commit/8451485e81092fcb058c8a6474830e431effe0c0))



# [1.5.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.4.0...v1.5.0) (2024-06-19)


### Bug Fixes

* AD Miner crash due tu wrongly formatted strings ([db44242](https://github.com/Mazars-Tech/AD_Miner/commit/db44242be617ff316adc55e1a17d416a28baaad6))
* Fix hover cards, donuts charts and search of disabled controls ([#145](https://github.com/Mazars-Tech/AD_Miner/issues/145)) ([64b67ae](https://github.com/Mazars-Tech/AD_Miner/commit/64b67ae7bd3ca5020d773b7d4a1a19520e979540))
* remove DA from users admin on computers control ([3b4753b](https://github.com/Mazars-Tech/AD_Miner/commit/3b4753b0a9cad510faa2861558a9e392e284aa0b))
* remove DC from path candidates and add non_da_dc request ([545de01](https://github.com/Mazars-Tech/AD_Miner/commit/545de01a43ff0f1868893753a57b35a8101a92ab))
* remove gmsa account from kerberoastable accounts ([aa0b3b6](https://github.com/Mazars-Tech/AD_Miner/commit/aa0b3b6fefa9d67b29937273cf00ef878b8fc422))
* unresolved bug during compromise OU request only deactivate the control and doesn't crash AD Miner ([19128f3](https://github.com/Mazars-Tech/AD_Miner/commit/19128f3efc8e9ff0b36f5a240001d464b72ee407))


### Features

* add warning when domain objects are missing from the database ([1859718](https://github.com/Mazars-Tech/AD_Miner/commit/18597182be01a0616e89d536afa022bcb64ca99a))


### Performance Improvements

* remove unused requests ([17d5a2c](https://github.com/Mazars-Tech/AD_Miner/commit/17d5a2c7e74adfe5b3ac975726aa4a44fc6f564d))



