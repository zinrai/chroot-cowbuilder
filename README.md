# cowbuilder-aide

cowbuilder-aide is a Python script that simplifies the creation and management of chroot environments using cowbuilder. It provides an interface for creating, updating, and logging into cowbuilder environments.

## Features

- Create new cowbuilder environments
- Update existing environments
- Log into environments
- Support for different distributions and architectures
- Custom roles for environment naming
- Verbose logging option

## Requirements

- cowbuilder
- sudo privileges

## Usage

### Create a new environment

```
$ ./cowbuilder-aide.py create -d sid -a amd64 --verbose
```

### Update an existing environment

```
$ ./cowbuilder-aide.py update -d sid -a amd64 --verbose
```

### Login an environment

```
$ ./cowbuilder-aide.py login -d sid -a amd64 --verbose
```

## License

This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/license/mit) for details.
