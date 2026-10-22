"""Shared accelerator guard.

PyTorch's MPS backend is not safe to drive from two threads at once (Metal asserts
"A command encoder is already encoding to this command buffer"). The detector runs on the
pipeline thread and the CLIP classifier on the judge worker thread, so both take this lock.
MLX (the VLM) has its own Metal queue and does not need it.
"""

import threading

torch_gpu_lock = threading.Lock()
