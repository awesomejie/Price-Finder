# Price-Finder
A project that matches product's price listings to the product

The project has its origin from the [Sortable's challenge](http://sortable.com/challenge/) 

Here is my Python solution. 

## Tested with environment
* Ubuntu 14.04 (64-bit)
* Python 2.7.11 
* pandas 0.17.1
* fuzzywuzzy 0.8.0 (installed via `pip install fuzzywuzzy`)
* nltk 3.1 (installed via `sudo pip install -U nltk`)

## Instructions
Git clone the project

```
git clone https://github.com/awesomejie/Price-Finder.git
```

Then cd into project folder and execute the command:

```
python main.py
```

That's it. Results in JSON format are generated in file "outputs.txt". 

To test on new datasets, replace "listings.txt" and "products.txt" in the data folder and run `python main.py`.
