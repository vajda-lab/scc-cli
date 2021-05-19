@_default:
    just --list

# installs/updates all dependencies
@bootstrap:
    pip install -U -r requirements.in

# invoked by continuous integration servers to run tests
@cibuild:
    echo "TODO: cibuild"

# opens a console
@console:
    echo "TODO: console"

# starts app
@server:
    echo "TODO: server"

# sets up a project to be used for the first time
@setup:
    just bootstrap

# runs tests
@test:
    echo "TODO: test"

# updates a project to run at its current version
@update:
    echo "TODO: update"
