# test-midas

Dear reviewer, glad to welcome you to this project.
If you have question about it, please, reach out me in [telegram](https://t.me/belousm).

To test the functionality of the code, try to run it with different configurations, follow these steps:

### Structure of project
```

├──LICENSE
├──README.md
├──dvc.lock
├──dvc.yaml
├──pyproject.toml
├──poetry.lock
├──data
│   ├──raw
│   │   └──BTCUSD_1_min_aver-src_cb_disk_.feather
│   ├──processed
│   │   ├──processed_trend_detection.feather
│   │   └──processed_volume_anomaly.feather
│   └──result
│       ├──result_trend_detection.feather
│       ├──result_volume_anomaly.feather
│       └──result_with_trend_and_anomaly.feather
├──notebooks
│   └──test_functions.ipynb
├──reports
│   ├──trends
│   └──volumes
└──src
    ├──feature
    │   ├──preprocessing_for_trend_detection.py
    │   └──preprocessing_for_volume_anomaly.py
    ├──models
    │   ├──concat.py
    │   ├──trend_detection.py
    │   └──volume_anomaly.py
    ├──utils
    │   ├──exception.py
    │   └──logger.py
    └──visualization
        ├──plots_for_trend.py
        └──plots_for_volume.py

```

### Stepd to run code
1. Clone repo 
```
git clone git@github.com:belousm/midas.git
```

2. Jump into progect repo 
```
cd midas
```
3. Install all dependencies 
```
poetry install
```
P.S.  If you don't have poetry you can install it by this command:
```
curl -sSL https://install.python-poetry.org | python3 -
```
4. Set an environment variable with the path to the project
```
export PATH_TO_TEST_MIDAS=$PWD
```

Now you can run all pipeline from scratch using dvc: 
```
dvc repro
```

Or you can run each step which you prefer: 
```
dvc run "stage name"
```

All stages names: 

1. `data_preprocessing_for_volume_anomaly`
2. `find_volume_anomaly`
3. `preprocessing_for_trend_detection`
4. `trend_detection`
5. `concat`
6. `plots_for_trend`

Also you can run any step from jupyter notebook using this command:
```
poetry run python $(dvc root)/src/{path_to_file} --config=$(dvc root)/params.yaml
```

### Data download
If you want to check already calculated data that has been produces, then you can run:
```
dvc pull
```

### Model setup
All parameters for modilng are stored in [params.yaml](https://github.com/belousm/midas/blob/master/params.yaml). So you can easily adjust model parameters.

### Examples result data
#### Examples for trend
![alt text](https://i.imgur.com/BWHVnH0.png)
![alt text](https://i.imgur.com/mM3uTLZ.png)
#### Examples for volume
![alt text](https://i.imgur.com/ldAD5bI.png)
