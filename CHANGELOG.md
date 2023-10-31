# [0.5.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.4.1...v0.5.0) (2023-10-31)


### Bug Fixes

* better error message ([12fd654](https://github.com/Mazars-Tech/AD_Miner/commit/12fd654794c65f4fb1c3f8fabea03cd38a155573))
* bugs with empty neo4j database ([dc6dc10](https://github.com/Mazars-Tech/AD_Miner/commit/dc6dc10b2ec420cd175d05f5d07485e8142bbd79))
* fix OS format for obsolete OS ([7f70296](https://github.com/Mazars-Tech/AD_Miner/commit/7f70296cbbac7c4c3f6bc4c8a4fcc498e5959c0f))
* fix visual bug on permission cards ([25dc2af](https://github.com/Mazars-Tech/AD_Miner/commit/25dc2af8bd2c1f5a8e9a69bdf39847ec95bfe4ef))
* remove broken and useless IOE buttons + fix users chart ([7ca4f9a](https://github.com/Mazars-Tech/AD_Miner/commit/7ca4f9ad6ad2e7f14ced6ec99336cde950d7efa8))


### Features

* add colors ([b5275a9](https://github.com/Mazars-Tech/AD_Miner/commit/b5275a9036daef508ace4789747b68d326cd32c3))
* add custom made edges to properties taken into account ([73f4351](https://github.com/Mazars-Tech/AD_Miner/commit/73f43518ceee06dfae78c6ca5c1a70088bdd90b2))
* add neo4j information message ([222cb3f](https://github.com/Mazars-Tech/AD_Miner/commit/222cb3f66b0a189d14c3c916ca6f46753ed0aaac))
* add os repartition chart ([3c8f5b4](https://github.com/Mazars-Tech/AD_Miner/commit/3c8f5b42f97b51814eb1ffc1277fff7044303437))
* adding cross domain privileges control ([1242dca](https://github.com/Mazars-Tech/AD_Miner/commit/1242dcab0668fa40244af0ceb3e9861b985c345e))
* ghost computer pages now displays pwdlastset attribute and whether the computer is enable or not ([f15898e](https://github.com/Mazars-Tech/AD_Miner/commit/f15898e70dd839c5305019020226989bbc5ae6f5))
* merge both unconstrainted delegation controls in one ([60f62d7](https://github.com/Mazars-Tech/AD_Miner/commit/60f62d7dd4df88f3a1775c6839871179c1e6dd4f))
* parallelize set_dcsync request ([ed711c7](https://github.com/Mazars-Tech/AD_Miner/commit/ed711c74b0afe125af911264f62e795915594137))
* small rework for dcsync control ([ac797ee](https://github.com/Mazars-Tech/AD_Miner/commit/ac797ee26afb9b92028afd1a7669148ba2d2b1f2))
* small rework for GPO ([99638f1](https://github.com/Mazars-Tech/AD_Miner/commit/99638f1e52fb26ce493740ffacee2b444545ea5e))



## [0.4.1](https://github.com/Mazars-Tech/AD_Miner/compare/v0.4.0...v0.4.1) (2023-10-18)


### Bug Fixes

* code typo crash AD Miner when disabling a request in config.json ([fdfd77a](https://github.com/Mazars-Tech/AD_Miner/commit/fdfd77aabd920ce473e58c136a96fe2f0d08ee5c))
* discord invitation link is now permanent ([2ff56b3](https://github.com/Mazars-Tech/AD_Miner/commit/2ff56b34303696009d233abc3937367679e0ad01))
* quick fail safe for da to da in case domains were not collected ([06e67ae](https://github.com/Mazars-Tech/AD_Miner/commit/06e67aea90f54e4aebc4736b33e5f7f2c70e0ce4))



# [0.4.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.3.0...v0.4.0) (2023-10-16)


### Bug Fixes

* bad request initialization with specific flags ([f2148d8](https://github.com/Mazars-Tech/AD_Miner/commit/f2148d875bcc6b71d963fb38de6cf2db9b203a17))
* bug with url encoding ([60df905](https://github.com/Mazars-Tech/AD_Miner/commit/60df905106a9d24125b3a324907ea248d01b8180))


### Features

* ctrl-c catching, new method for parallel write queries & potential bug fix ([d3990f4](https://github.com/Mazars-Tech/AD_Miner/commit/d3990f4b531bc51dbc508f8985a9b266187c47dd))


### Performance Improvements

* remove 7 useless requests ([f04e1e6](https://github.com/Mazars-Tech/AD_Miner/commit/f04e1e6f3f10fe0d0cc4f846e21210d99c9ca660))



# [0.3.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.2.1...v0.3.0) (2023-10-11)


### Bug Fixes

* add failsaves for domains missing ([b356841](https://github.com/Mazars-Tech/AD_Miner/commit/b35684168987aa6a528594aa9e3cc48c356b5bb7))
* comment request and remove entry in config ([1f6f2cf](https://github.com/Mazars-Tech/AD_Miner/commit/1f6f2cf965f1cf042db2df0f976e8af5f2e93fbe))
* group anomaly acl bug ([7bf0d64](https://github.com/Mazars-Tech/AD_Miner/commit/7bf0d64203b476845001108e069147727861606f))
* hide list when closing search bar ([52d1e85](https://github.com/Mazars-Tech/AD_Miner/commit/52d1e85e4603c7201f3a25008e2e6103d25ffc7c))
* remove old comment ([bbd3c21](https://github.com/Mazars-Tech/AD_Miner/commit/bbd3c21f8aca77476074db1a4c38453a464b8b2f))
* remove unused request that could cause some crash ([b2b734a](https://github.com/Mazars-Tech/AD_Miner/commit/b2b734aaf0649ac1c6df2a700b044614627c9e47))


### Features

* add animation, auto-focus and highlight ([12580b2](https://github.com/Mazars-Tech/AD_Miner/commit/12580b2eebff273e6602dab1ef77cb06a22cb6d4))
* search bar on main page ([f50b539](https://github.com/Mazars-Tech/AD_Miner/commit/f50b539284b712f703dcbfd89f1644d9ab109779))



## [0.2.1](https://github.com/Mazars-Tech/AD_Miner/compare/v0.2.0...v0.2.1) (2023-10-05)


### Bug Fixes

* two typos ([eaa36d9](https://github.com/Mazars-Tech/AD_Miner/commit/eaa36d9284f1a53a6f034ec33ff38725e5e72ce1))



