#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

show_help() {
    cat <<EOM
Invocation:

    $0 [-h|-?] [-s] [-u USER] [-e EXECUTABLE] [--] [ARGS...]

Options:

    -h|-?         : Display this help text
    -s            : Elevate this script to run Docker as root
                    (default: false)
    -u USER       : User parameter to pass on to docker run
                    (default: current UID / GID)
    -e EXECUTABLE : Entrypoint to pass on to docker run
                    (default: none)
    ARGS          : Arguments for the dockerized process
EOM
}

##### Option parsing #####
AS_ROOT=false
USER=$(id -u):$(id -g)
ENTRYPOINT=

while getopts "h?su:e:" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    s)  AS_ROOT=true
        ;;
    u)  USER=$OPTARG
        ;;
    e)  ENTRYPOINT=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

if [[ "${1:-}" = "--" ]]; then
    shift
fi

##### Elevate script #####
if [[ $AS_ROOT = true && $UID -ne 0 ]]; then
    sudo "$0" -u "$USER" -e "$ENTRYPOINT" "$@"
    exit
fi

##### Build container #####
CONTAINER_NAME=volunteers-test
docker build --pull -t "$CONTAINER_NAME" ci

##### Run container #####
ADDITIONAL_ARGS=
EXEC_ARGS=
if [[ -n "$ENTRYPOINT" ]]; then
    ADDITIONAL_ARGS="--entrypoint $ENTRYPOINT"
fi
if [[ $# -gt 0 ]]; then
    EXEC_ARGS="$*"
fi
docker run \
    -v "$PWD:$PWD" \
    --rm \
    --name "$CONTAINER_NAME" \
    --workdir "$PWD" \
    --user "$USER" \
    $ADDITIONAL_ARGS \
    "$CONTAINER_NAME" \
    $EXEC_ARGS

