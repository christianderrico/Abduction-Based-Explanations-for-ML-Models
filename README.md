# Abduction-Based-Explanations-for-ML-Models

Reproduction of the study "Alexey Ignatiev, Nina Narodytska, Joao Marques-Silva. *Abduction-Based Explanations for Machine Learning Models*"

## Getting Started

The following packages are necessary to run the code:

* [numpy](http://www.numpy.org/)
* [pandas](https://pandas.pydata.org/)
* [cplex](https://pypi.org/project/cplex/)
* [pySMT](https://github.com/pysmt/pysmt) (with Z3 installed)
* [pySAT](https://github.com/pysathq/pysat)
* [matplotlib](https://matplotlib.org/)
* [scikit-learn](https://scikit-learn.org/stable/)
* [keras](https://pypi.org/project/keras/)
* [tensorflow](https://www.tensorflow.org/)
* [tensorflow_docs](https://github.com/tensorflow/docs)

## Usage
The script has a number of parameters, which can be set from the command line. To see the list of options, run (the executable script is located in src):
```
$ main.py -h
```

### Datasets

The script uses datasets in the CSV format. They are in the **dataset_files**. For this, you need to do a few steps:

1. Assume your dataset is stored in file ```datasets_files/dataset.csv```.
2. Create another file named ```somepath/dataset.csv.catcol``` that contains the indices of the categorical columns of ```somepath/dataset.csv```. For instance, if columns ```0```, ```1```, and ```5``` contain categorical data, the file should contain the lines
