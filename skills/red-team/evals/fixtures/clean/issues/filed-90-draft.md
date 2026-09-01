# Filed during the wave: the campaign anchor is frozen at generation time

The campaign receipt binds its anchor to the commit that introduced the fixtures:

    "skill_tree_sha256_evaluated": FROZEN_AT_CAMPAIGN,

so re-running the producer against a moved tree reproduces the committed bytes
rather than overwriting them.
