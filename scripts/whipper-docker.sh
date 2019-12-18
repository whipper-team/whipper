#!/bin/sh
CD_DEVICE="/dev/cdrom"
OUTPUT_DIR="${HOME}/Music"

PERSONAL_CONF_DIR="${HOME}/.config/whipper"
WRAPPER_CONFIG_FILE="${HOME}/.config/whipper_wrapper"

if [ -e "${WRAPPER_CONFIG_FILE}" ] ; then
  . "${WRAPPER_CONFIG_FILE}"
fi

if [ ! -e "${CD_DEVICE}" ] ; then
  echo "Could not file CD device: ${CD_DEVICE}" 1>&2
  exit 2
fi

if [ ! -d "${OUTPUT_DIR}" } ; then
  echo "Cannot access ${OUTPUT_DIR}" 1>&2
  exit 2
fi


if [ ! -d "${PERSONAL_CONF_DIR}" ] ; then
  echo "Creating ${PERSONAL_CONF_DIR} directory"
  if ! mkdir -p "${PERSONAL_CONF_DIR}" ; then
    echo "Failed to create ${PERSONAL_CONF_DIR}" 1>&2
    exit 2
  fi
fi

docker run -ti --rm \
  --device="${CD_DEVICE}" \
  -v "${PERSONAL_CONF_DIR}":/home/worker/.config/whipper \
  -v "${OUTPUT_DIR}":/home/worker/output \
  whipperteam/whipper "${@}"
