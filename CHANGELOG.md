# [1.3.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.2.0...v1.3.0) (2024-05-28)


### Bug Fixes

* clean ADLocalGroup objects to avoid acl_anomaly bug ([92c7a90](https://github.com/Mazars-Tech/AD_Miner/commit/92c7a900688174165cf7a54588c23e7ef2ce88cf))
* rating crash on NoneType pwdlastset ([55705cf](https://github.com/Mazars-Tech/AD_Miner/commit/55705cf3526ac10aeeec1f01e88089029a9cef92))
* update offline main page charts script ([511ddbb](https://github.com/Mazars-Tech/AD_Miner/commit/511ddbbb477d9d057495dedd3e5d755d9dcd9058))


### Features

* rework of OU control ([830936e](https://github.com/Mazars-Tech/AD_Miner/commit/830936edd6ef138ad6e348ce25870e6b2bc73021))



# [1.2.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.1.0...v1.2.0) (2024-03-12)


### Features

* update requests.json ([589eb7b](https://github.com/Mazars-Tech/AD_Miner/commit/589eb7bcd0f7b0f1290c94ed878718054c85370c))



# [1.1.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.0.0...v1.1.0) (2024-02-15)


### Bug Fixes

* better request for low privilege impersonation ([#121](https://github.com/Mazars-Tech/AD_Miner/issues/121)) ([71ceb57](https://github.com/Mazars-Tech/AD_Miner/commit/71ceb571d8526fa888cb029c40faa6be78658ee8))
* bug with u.name ([#123](https://github.com/Mazars-Tech/AD_Miner/issues/123)) ([26cb9d8](https://github.com/Mazars-Tech/AD_Miner/commit/26cb9d873eda64c0e874b9ba9b2585c81ace6382))
* bugs with charts and azure data ([#114](https://github.com/Mazars-Tech/AD_Miner/issues/114)) ([7523229](https://github.com/Mazars-Tech/AD_Miner/commit/7523229e2c6873c66ba30f9101fbf3ce0426cc68))
* correct spelling of GPLink to take it into account when computing paths ([337320d](https://github.com/Mazars-Tech/AD_Miner/commit/337320d64293f18c61cf281a6b8e6f8cd87c2b76))
* fix typo in request leading to missing DCs ([#118](https://github.com/Mazars-Tech/AD_Miner/issues/118)) ([3867f20](https://github.com/Mazars-Tech/AD_Miner/commit/3867f2045d3412f5830c63bb59aadc7c372895d6))


### Features

* adding fgpp control ([#113](https://github.com/Mazars-Tech/AD_Miner/issues/113)) ([6431abf](https://github.com/Mazars-Tech/AD_Miner/commit/6431abf00c945c40fb4e9714af01c22d4dc6a751))
* smartest path ([#119](https://github.com/Mazars-Tech/AD_Miner/issues/119)) ([2d59408](https://github.com/Mazars-Tech/AD_Miner/commit/2d5940813cf950056bf7e857138af820a1ec4042))


### Performance Improvements

* parallelization of the rdp request ([#122](https://github.com/Mazars-Tech/AD_Miner/issues/122)) ([5d18ab0](https://github.com/Mazars-Tech/AD_Miner/commit/5d18ab0e87d0b24d515a37dfedc0e5111568f817))



# [1.0.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.7.0...v1.0.0) (2023-12-20)


* BREAKING CHANGE: bump to version 1.0.0 ([cf0d0f5](https://github.com/Mazars-Tech/AD_Miner/commit/cf0d0f542e51e7cd34ef84efcb0d0d1fea0e8ba4))


### BREAKING CHANGES

* bump to version 1.0.0



# [0.7.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.6.0...v0.7.0) (2023-12-20)


### Bug Fixes

* changing alignment of titles in firefox ([013a283](https://github.com/Mazars-Tech/AD_Miner/commit/013a28325224d8e0d29291849d2505197117a2a3))
* Fix bug with 'Base' labels in neo4j databases ([82541be](https://github.com/Mazars-Tech/AD_Miner/commit/82541be0a2f57fee025a2db740087a43c34a318d))
* fixing donut js ([a07deaf](https://github.com/Mazars-Tech/AD_Miner/commit/a07deafdee838dd10c690fad56cf7509a1e53c54))
* more logical calculation of ghost computers ([a359e38](https://github.com/Mazars-Tech/AD_Miner/commit/a359e38f719b59348b488e6b9f249ccec7cca032))
* paths to Operators groups ([#110](https://github.com/Mazars-Tech/AD_Miner/issues/110)) ([239cada](https://github.com/Mazars-Tech/AD_Miner/commit/239cada9895b6bdec7a8639e7083184394ef62d5))
* temporary fix to enable serialization of neo4j datetime objects ([3695d9e](https://github.com/Mazars-Tech/AD_Miner/commit/3695d9e5c456b53c07b30df0d07e02b5d31d0ee5))


### Features

* changing on prem background circle ([3952bff](https://github.com/Mazars-Tech/AD_Miner/commit/3952bff05ca6bb23e352be863db36348b87784f7))
* changing the azure circle ([70a49c4](https://github.com/Mazars-Tech/AD_Miner/commit/70a49c41502373c69e58a030ed79d96e017f5dd2))
* Kerberos unconstrained delegation control rework ([0eef50f](https://github.com/Mazars-Tech/AD_Miner/commit/0eef50f2c81f97467fa86bd372b1f68021da8974))
* **main_page:** init version of automatic hexagon placement ([59864b1](https://github.com/Mazars-Tech/AD_Miner/commit/59864b125fb142996f30757bf49babece28e43c5))
* new icons ([5f3d80e](https://github.com/Mazars-Tech/AD_Miner/commit/5f3d80eb6c2b605380f8979d2c7931b846d96186))



