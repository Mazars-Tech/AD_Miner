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



# [1.4.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.3.0...v1.4.0) (2024-06-06)


### Bug Fixes

* crash when generating reports ([#143](https://github.com/Mazars-Tech/AD_Miner/issues/143)) ([61fefd5](https://github.com/Mazars-Tech/AD_Miner/commit/61fefd5eecf4e1ff4ed8bb04663982fde44c420a))
* switch AZ / onprem and AD Miner not displayed ([a15367e](https://github.com/Mazars-Tech/AD_Miner/commit/a15367ef3472b1cd37cdac29700a170589cc4162))
* windows compatibility ([ceaa481](https://github.com/Mazars-Tech/AD_Miner/commit/ceaa48137c3e958fca3ed6fd8d066a2b638debf6))


### Features

* Stylised edges between different domains ([#142](https://github.com/Mazars-Tech/AD_Miner/issues/142)) ([b15b5e9](https://github.com/Mazars-Tech/AD_Miner/commit/b15b5e9e5a899e70121df627ae3af75b3f646f8b))



