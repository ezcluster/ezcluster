# HDP module

## Expected repository layout:

``` 
.
├── ambari
│   └── centos7
│       └── 2.x
│           └── updates
│               └── 2.6.2.2
│                   ├── ambari
│                   ├── repodata
│                   ├── RPM-GPG-KEY
│                   ├── smartsense
│                   └── tars
│                       ├── ambari
│                       └── smartsense
├── HDP
│   └── centos7
│       └── 2.x
│           └── updates
│               └── 2.6.5.0
│                   ├── accumulo
│                   ├── atlas
│                   ├── bigtop-jsvc
│                   ├── bigtop-tomcat
│                   ├── datafu
│                   ├── druid
│                   ├── falcon
│                   ├── flume
│                   ├── hadoop
│                   ├── hbase
│                   ├── hdp-select
│                   ├── hive
│                   ├── hive2
│                   ├── hue
│                   ├── kafka
│                   ├── knox
│                   ├── livy
│                   ├── mahout
│                   ├── oozie
│                   ├── phoenix
│                   ├── pig
│                   ├── ranger
│                   ├── repodata
│                   ├── RPM-GPG-KEY
│                   ├── shc
│                   ├── slider
│                   ├── slider-app-packages
│                   ├── spark
│                   ├── spark2
│                   ├── spark_llap
│                   ├── sqoop
│                   ├── storm
│                   ├── superset
│                   ├── tez
│                   ├── tez_hive2
│                   ├── vrpms
│                   │   ├── accumulo
│                   │   ├── atlas
│                   │   ├── datafu
│                   │   ├── druid
│                   │   ├── falcon
│                   │   ├── flume
│                   │   ├── hadoop
│                   │   ├── hbase
│                   │   ├── hive
│                   │   ├── hive2
│                   │   ├── kafka
│                   │   ├── knox
│                   │   ├── livy
│                   │   ├── mahout
│                   │   ├── oozie
│                   │   ├── phoenix
│                   │   ├── pig
│                   │   ├── ranger
│                   │   ├── shc
│                   │   ├── slider
│                   │   ├── spark
│                   │   ├── spark2
│                   │   ├── spark_llap
│                   │   ├── sqoop
│                   │   ├── storm
│                   │   ├── superset
│                   │   ├── tez
│                   │   ├── tez_hive2
│                   │   ├── zeppelin
│                   │   └── zookeeper
│                   ├── zeppelin
│                   └── zookeeper
├── HDP-GPL
│   └── centos7
│       └── 2.x
│           └── updates
│               └── 2.6.5.0
│                   ├── hadooplzo
│                   ├── repodata
│                   ├── RPM-GPG-KEY
│                   └── vrpms
│                       └── hadooplzo
└── HDP-UTILS-1.1.0.22
    └── repos
        └── centos7
            ├── openblas
            ├── repodata
            ├── RPM-GPG-KEY
            └── snappy

102 directories
```
