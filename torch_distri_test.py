import torch
import torch.distributed as dist
import os
import time

def setup(rank, world_size, master_addr, master_port):
    os.environ['MASTER_ADDR'] = master_addr
    os.environ['MASTER_PORT'] = master_port
    # Initialize the process group
    # Ensure backend is 'gloo' if on CPU, or 'nccl' if on CUDA and it's installed
    backend = 'gloo' # or 'nccl' if you have GPUs and NCCL
    dist.init_process_group(backend, rank=rank, world_size=world_size)
    print(f"Rank {rank} initialized with backend {backend} on {os.uname()[1]}.")

def cleanup():
    dist.destroy_process_group()
    print(f"Rank {dist.get_rank()} cleaned up on {os.uname()[1]}.")

def main():
    # These should be set by torchrun
    rank = int(os.environ['RANK'])
    world_size = int(os.environ['WORLD_SIZE'])
    local_rank = int(os.environ['LOCAL_RANK']) # torchrun provides this

    master_addr = os.environ['MASTER_ADDR']
    master_port = os.environ['MASTER_PORT']

    print(f"Starting Rank {rank}/{world_size} (Local Rank {local_rank}) on {os.uname()[1]} | MASTER_ADDR={master_addr} MASTER_PORT={master_port}")

    try:
        setup(rank, world_size, master_addr, master_port)

        # Create a tensor on the default device for the rank
        if dist.get_backend() == "nccl": # If using GPUs
            device = torch.device(f"cuda:{local_rank}")
            torch.cuda.set_device(device)
            tensor = torch.ones(1, device=device) * (rank + 1)
        else: # CPU
            tensor = torch.ones(1) * (rank + 1)

        print(f"Rank {rank} on {os.uname()[1]} has tensor: {tensor.item()}")

        # Perform a simple all-reduce
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
        print(f"Rank {rank} on {os.uname()[1]} after all_reduce has tensor: {tensor.item()}")

        # Simulate some work
        time.sleep(5)

        # Explicit barrier before cleanup (good practice)
        print(f"Rank {rank} on {os.uname()[1]} reaching main barrier.")
        dist.barrier()
        print(f"Rank {rank} on {os.uname()[1]} passed main barrier.")

    except Exception as e:
        print(f"Rank {rank} on {os.uname()[1]} encountered an error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        print(f"Rank {rank} on {os.uname()[1]} proceeding to cleanup.", flush=True)
        cleanup()
        print(f"Rank {rank} on {os.uname()[1]} finished.", flush=True)

if __name__ == '__main__':
    main()
