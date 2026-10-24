"""Rank candidate offsets; a model lookup never confirms a drive offset."""

from whipper.common.drive_offsets_data import MODEL_OFFSETS


def known_offsets_for(vendor, model):
    """Match the complete vendor/model name, ignoring case and whitespace."""
    if not vendor or not model:
        return []
    name = '{} - {}'.format(
        ' '.join(vendor.upper().split()), ' '.join(model.upper().split()))
    return [offset for offset, count in MODEL_OFFSETS.get(name, ())]


def order_offsets(offsets, configured=None, known=(), prioritize=True):
    """Prepend hints when requested, preserving order and removing repeats."""
    prefix = []
    if prioritize:
        if configured is not None:
            prefix.append(configured)
        prefix.extend(known)
    return list(dict.fromkeys(prefix + list(offsets)))
