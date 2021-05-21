#!/usr/bin/env bash

set -o errexit -o nounset

usage() {
    cat >&2 << 'EOF'
./test.bash "$ldi_linz_key" "$ldi_mfe_key" "$ldi_nzdf_key" "$ldi_basemaps_key"
EOF
}

arguments="$(getopt --options '' --longoptions help --name "$0" -- "$@")"
eval set -- "$arguments"
unset arguments

while true
do
    case "$1" in
        --help)
            usage
            exit
            ;;
        --)
            shift
            break
            ;;
        *)
            printf 'Not implemented: %q\n' "$1" >&2
            exit 1
            ;;
    esac
done

if [[ $# -ne 4 ]]
then
    usage
    exit 2
fi

export LDI_LINZ_KEY="$1"
export LDI_MFE_KEY="$2"
export LDI_NZDF_KEY="$3"
export LDI_BASEMAPS_KEY="$4"

image='qgis/qgis'
qgis_version_tag='latest'
plugin_name='linz-data-importer'
image_name="${image}:${qgis_version_tag}"
container_name="${image/\//-}-${qgis_version_tag}"

cleanup() {
    docker stop "$container_name"
}
trap cleanup EXIT

docker run \
    --detach \
    --name="$container_name" \
    --volume="${PWD}:/tests_directory" \
    --env=LDI_LINZ_KEY \
    --env=LDI_MFE_KEY \
    --env=LDI_NZDF_KEY \
    --env=LDI_BASEMAPS_KEY \
    --env=DISPLAY=:99 \
    --pull=always \
    --rm \
    "$image_name"
sleep 10
docker exec "$container_name" qgis_setup.sh "$plugin_name"

docker exec -t "$container_name" qgis_testrunner.sh "${plugin_name}.tests.run_tests.run_test_modules"
