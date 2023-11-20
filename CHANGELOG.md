# [0.6.0](https://github.com/Mazars-Tech/AD_Miner/compare/v0.5.0...v0.6.0) (2023-11-20)


### Bug Fixes

* add label in neo4j request ([2dfbf4e](https://github.com/Mazars-Tech/AD_Miner/commit/2dfbf4e3463a54e0ed593f1f7ae3ab6f3a39604c))
* bug with if condition admin of computer ([4b5ac15](https://github.com/Mazars-Tech/AD_Miner/commit/4b5ac158fd631052ad3677489125d632f7802b3c))
* bug with split name and label ([d3475e0](https://github.com/Mazars-Tech/AD_Miner/commit/d3475e0ff8ede44fdf52307cd5fcc84957647325))
* bug with upper ([733f0d0](https://github.com/Mazars-Tech/AD_Miner/commit/733f0d00300f1f253a70f7ad7d19cede0c1ce367))
* change value on tooltip ([dc960a6](https://github.com/Mazars-Tech/AD_Miner/commit/dc960a6eae7541b43042cdedb37bb9e2d598f038))
* decimal bug ([209a7bb](https://github.com/Mazars-Tech/AD_Miner/commit/209a7bb42eeb27110bf4349026a0cf6fe41bcf85))
* dont add only protected users to da ([12618f3](https://github.com/Mazars-Tech/AD_Miner/commit/12618f3b3ea5af1260373ff8a5b6b20b82c1c724))
* fix infinite bug ([eb0168d](https://github.com/Mazars-Tech/AD_Miner/commit/eb0168d0f10a154a4691d1539c6628fa0fcf3bc2))
* fix non display for zero values on log scale ([957779e](https://github.com/Mazars-Tech/AD_Miner/commit/957779e7fc432ebdc53c0fedffdb4448e21c6875))
* putting back rbcd in config ([d78cd47](https://github.com/Mazars-Tech/AD_Miner/commit/d78cd4703bc85ec3accbc2ac8502ec0717e7a54a))
* rating now take into account the oldest krbtgt password change ([070c58b](https://github.com/Mazars-Tech/AD_Miner/commit/070c58ba3ab6f87967c07f5a7b24380569f58ad3))
* remove new pre request ([608e8e2](https://github.com/Mazars-Tech/AD_Miner/commit/608e8e2ea6a299adc8d32ae56836630c98dafb7d))
* remove print ([919da6a](https://github.com/Mazars-Tech/AD_Miner/commit/919da6a02621c985de2c91e1c14af5728ced3736))
* remove trailing spaces ([cba881a](https://github.com/Mazars-Tech/AD_Miner/commit/cba881a7ef5b917bc0e004434dc3afa497e133c4))
* rename group anomaly ACL to anomaly ACL ([c39ef0b](https://github.com/Mazars-Tech/AD_Miner/commit/c39ef0be190b8c81df196e753344eb6ecd69c23f))
* repair broken config.json file ([e13e5dd](https://github.com/Mazars-Tech/AD_Miner/commit/e13e5dd8301ee7ad3f5ff8fcd1a2d9ff1df1b9cc))


### Features

* Add 5 new controls from "primaryGroupID_lower_than_1000" to "up_to_date_admincount" ([795a5a9](https://github.com/Mazars-Tech/AD_Miner/commit/795a5a94db44707faa2f5aebb4fbed25f679603d))
* add a pre request ([1b74e17](https://github.com/Mazars-Tech/AD_Miner/commit/1b74e1751b4c42bb1054bb047cff42cee769b388))
* add admincount control page ([265b0af](https://github.com/Mazars-Tech/AD_Miner/commit/265b0afb7ffc08b5da771d938f6129021fb07a14))
* add error message ([90e39f1](https://github.com/Mazars-Tech/AD_Miner/commit/90e39f19f3d6217dd6ebe622ab20e221b88e7b74))
* add get_label_icon_dictionary ([5a2a4d9](https://github.com/Mazars-Tech/AD_Miner/commit/5a2a4d9f37e5169c54a9ebf822934ea19d4fb717))
* add guest account enabled control ([2dfeff6](https://github.com/Mazars-Tech/AD_Miner/commit/2dfeff668503afd56c95611ab1c4101c9431d296))
* add log scale button for evolution graph ([a7cdce4](https://github.com/Mazars-Tech/AD_Miner/commit/a7cdce4d24d2d6f8586aa3e2191858f53f2e4cae))
* Add Louis in the list of contributors ([c334c40](https://github.com/Mazars-Tech/AD_Miner/commit/c334c40686acae238d0c732d1968dd052a6a67ca))
* add misc category ([9af600f](https://github.com/Mazars-Tech/AD_Miner/commit/9af600f5a9329c90fd0aa2bdfe7e30ca752a92fe))
* Add preWin2000 control ([575391e](https://github.com/Mazars-Tech/AD_Miner/commit/575391ed91cbb1ab65de235f540a2a22b185e157))
* add Protected Users control ([a0bf823](https://github.com/Mazars-Tech/AD_Miner/commit/a0bf823866907ca00dc6ce019a9435d1d7b440af))
* add SID control ([d74c301](https://github.com/Mazars-Tech/AD_Miner/commit/d74c3013c925fb497cbfbd00951c5f8d0be00835))
* add small evolution percentage ([4ae7982](https://github.com/Mazars-Tech/AD_Miner/commit/4ae798251547a935225340c545355d606f260acd))
* better background ([43bcf9c](https://github.com/Mazars-Tech/AD_Miner/commit/43bcf9c0291a266a7d0ffd64b4ec73ba0c18272c))
* better opacity ([a739fad](https://github.com/Mazars-Tech/AD_Miner/commit/a739fad2478fa80178ad956f0dc865031ab96d85))
* better svg main_circle ([6cdf4bc](https://github.com/Mazars-Tech/AD_Miner/commit/6cdf4bc756a11dd150cb5cba651a2d015c9e7f2a))
* evolution data for admincount with sum of indicators ([44ff6a2](https://github.com/Mazars-Tech/AD_Miner/commit/44ff6a272007187b2c90e1c3092315e286c59c2c))
* ghost DC displayed first in DC list, add lastlogon column ([7f0af53](https://github.com/Mazars-Tech/AD_Miner/commit/7f0af535d83318cb981aa8b1f8ac1ddf1bd2637d))
* improve description for ACL anomaly ([0c1da89](https://github.com/Mazars-Tech/AD_Miner/commit/0c1da8972aa2191494559f6aa658322da092f0ef))
* improve search bar highlighting hovered controls and closing the menu when clicking outside ([7d2da03](https://github.com/Mazars-Tech/AD_Miner/commit/7d2da036496dcc712a8b49de9170a30d5896fc3d))
* minimize neo4j requests used by new controles ([916cbf1](https://github.com/Mazars-Tech/AD_Miner/commit/916cbf1d31635ae4aa2d67660b93e22bfe2c6aa8))
* new neo4j requests ([a902de9](https://github.com/Mazars-Tech/AD_Miner/commit/a902de99c81bb3fcb7a6238bef1daf2466dd0d19))
* split schema and key admin + add protected users on DA page ([6c6e5af](https://github.com/Mazars-Tech/AD_Miner/commit/6c6e5af32f96bf9d23021e259bb0967d8c4518d2))


### Performance Improvements

* better known SIDs ([b5e2f90](https://github.com/Mazars-Tech/AD_Miner/commit/b5e2f900590896a745fb175427912817cebba29c))



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



