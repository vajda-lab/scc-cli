# SCC-CLI README

## Install 

```shell
# while the project is private
$ pip install git+ssh://git@github.com/vajda-lab/scc-cli.git#egg=scc-cli

# when the library is on pypi
$ pip install vajadalab-scc-cli
```

## Usage

```shell
$ scccli --help
```

## Setup

First register an account at the SCC_API_URL provided.
Then, login to get your access token.

```shell
$ scccli init <access token>
```
