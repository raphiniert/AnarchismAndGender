# Anarchism and gender

This project is a tool to analyse short text corpora, namely historical 
Austrian newspaper articles. Newspapers are, amongst other file formats, 
available as text files via the ANNO tool (see http://anno.onb.ac.at) provided
by the Austrian National Library. The project is part of an undergraduate 
seminar (see https://ufind.univie.ac.at/de/course.html?lv=070137&semester=2020W) 
at the University of Vienna. The seminar deals with anarchism and gender. 

## prerequisites

* Working python 3.7+ installation (https://www.python.org/downloads/)

Open a terminal and check your current Python 3 version by running:
```shell script
python3 -V
Python 3.7.3  # 3.8.X is also fine
```

## project setup

### download project

Open a terminal, clone the project, enter the project folder and create the log
directory:

```shell script
git clone https://github.com/raphiniert/AnarchismAndGender.git
cd AnarchismAndGender
mkdir log
```

### setup virtual environment and install dependencies

Enter the project folder an execute following steps:

```shell script
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download de_core_news_lg
```

Verify if everything worked by running:

```shell script
python main.py -h
```

If you see the following output, you're good to go.

```shell script
usage: main.py [-h] [--verbose]

optional arguments:
  -h, --help  show this help message and exit
  --verbose   increase output verbosity
```

## troubleshooting

Below you find common errors and possible solutions to fix them.

#### `SyntaxError: invalid syntax` or `ModuleNotFoundError: No module named 'selenium'`
Make sure your virtual environment is enabled.
You can enable it by running:
```shell script
. venv/bin/activate
```

#### `FileNotFoundError: [Errno 2] No such file or directory: '/path/to/project/log/*anarchism.log'`
Make sure the log folder exists.
You can create it by running:
```shell script
mkdir log
```