import os, site, sys

def add_vendor_lib():
    """
    Add the vendored dependencies to sys.path.

    Uses ``site.addsitedir`` so that pth files, if any, in the vendor lib will
    be processed.

    Places new path entries at the beginning of sys.path so system-installed
    libs can't shadow them and cause hard-to-debug problems.

    """
    old_sys_path = set(sys.path)

    vendor_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "vendor",
        )

    site.addsitedir(vendor_dir)

    new_sys_path = []
    for item in sys.path:
        if item not in old_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)

    sys.path[:0] = new_sys_path
