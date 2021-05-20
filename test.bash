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

LDI_LINZ_KEY="$1"
LDI_MFE_KEY="$2"
LDI_NZDF_KEY="$3"
LDI_BASEMAPS_KEY="$4"

image='elpaso/qgis-testing-environment'
qgis_version_tag='master'
plugin_name='linz-data-importer'

container_name='qgis-testing-environment'

cleanup() {
    docker stop "$container_name"
}
trap cleanup EXIT

docker pull "${image}:${qgis_version_tag}"

docker run -d --name "$container_name" \
  -v "${PWD}:/tests_directory" \
  -e LDI_LINZ_KEY \
  -e LDI_MFE_KEY \
  -e LDI_NZDF_KEY \
  -e LDI_BASEMAPS_KEY \
  -e DISPLAY=:99 \
  "${image}:${qgis_version_tag}"
sleep 10
docker exec "$container_name" sh -c "qgis_setup.sh ${plugin_name}"
docker exec "$container_name" sh -c "ln -s /tests_directory /root/.local/share/QGIS/QGIS3/profiles/default/${plugin_name}"

docker exec -t "$container_name" sh -c "qgis_testrunner.sh ${plugin_name}.tests.run_tests.run_test_modules"
