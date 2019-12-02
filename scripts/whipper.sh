#!/usr/bin/env bash
CD_DEVICE="/dev/cdrom"
OUTPUT_DIR="${HOME}/Music"

WRAPPER_CONFIG_FILE="${HOME}/.config/whipper_wrapper"
if [ -e "${WRAPPER_CONFIG_FILE}" ] ; then
  . ${WRAPPER_CONFIG_FILE}
fi

if [ ! -e "${CD_DEVICE}" ] ; then
  echo "Could not file CD device: ${CD_DEVICE}" 1>&2
  exit 2
fi

PERSONAL_CONF_DIR="${HOME}/.config/whipper"
if [ ! -d "${PERSONAL_CONF_DIR}" ] ; then
  echo "Creating ${PERSONAL_CONF_DIR} directory"
  mkdir -p "${PERSONAL_CONF_DIR}"
  if [ $? -ne 0 ] ; then
    echo "Failed to create ${PERSONAL_CONF_DIR}" 1>&2
    exit 2
  fi
fi

docker run -ti --rm \
  --device="${CD_DEVICE}" \
  -v "${PERSONAL_CONF_DIR}":/home/worker/.config/whipper \
  -v "${OUTPUT_DIR}":/home/worker/output \
  whipperteam/whipper ${@}
