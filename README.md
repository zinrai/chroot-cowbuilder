# cowbuilder-aide

cowbuilder-aide is a Python script that simplifies the creation and management of chroot environments using cowbuilder. It provides an interface for creating, updating, and logging into cowbuilder environments.

## Features

- Create new cowbuilder environments
- Update existing environments
- Log into environments
- Support for different distributions and architectures
- Custom roles for environment naming
- Pass additional cowbuilder options directly

## Requirements

- cowbuilder
- sudo privileges

## Usage

### Create a new environment

```
$ ./cowbuilder-aide.py create -d sid -a amd64
```

### Update an existing environment

```
$ ./cowbuilder-aide.py update -d sid -a amd64
```

### Login to an environment

```
$ ./cowbuilder-aide.py login -d sid -a amd64
```

### Using additional cowbuilder options

You can pass additional options directly to cowbuilder by using `--` followed by the options:

```
$ ./cowbuilder-aide.py create -d bookworm -a amd64 -- --mirror http://ftp.jp.debian.org/debian --debootstrapopts --variant=minbase
```

```
$ ./cowbuilder-aide.py login -d bookworm -a amd64 -- --save-after-login
```

## Configuration

The script uses `/var/cache/pbuilder/` to store cow images. Ensure that the user running the script has the necessary permissions to write to this directory or run the script with sudo.

## License

This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/license/mit) for details.
