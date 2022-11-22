# test-midas

Dear reviewer, glad to welcome you to this project.

To test the functionality of the code, try to run it with different configurations, follow these steps:

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

All parameters for modilng are stored in [params.yaml](https://github.com/belousm/midas/blob/master/params.yaml). So you can easily adjust model parameters.
