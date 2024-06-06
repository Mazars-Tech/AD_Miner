# [1.4.0](https://github.com/Mazars-Tech/AD_Miner/compare/v1.3.0...v1.4.0) (2024-06-06)


### Bug Fixes

* crash when generating reports ([#143](https://github.com/Mazars-Tech/AD_Miner/issues/143)) ([61fefd5](https://github.com/Mazars-Tech/AD_Miner/commit/61fefd5eecf4e1ff4ed8bb04663982fde44c420a))
* switch AZ / onprem and AD Miner not displayed ([a15367e](https://github.com/Mazars-Tech/AD_Miner/commit/a15367ef3472b1cd37cdac29700a170589cc4162))
* windows compatibility ([ceaa481](https://github.com/Mazars-Tech/AD_Miner/commit/ceaa48137c3e958fca3ed6fd8d066a2b638debf6))


### Features

* Stylised edges between different domains ([#142](https://github.com/Mazars-Tech/AD_Miner/issues/142)) ([b15b5e9](https://github.com/Mazars-Tech/AD_Miner/commit/b15b5e9e5a899e70121df627ae3af75b3f646f8b))



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



