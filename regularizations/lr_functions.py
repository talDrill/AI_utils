import torch

def create_scheduler(optimizer, scheduler_method : str):
    if scheduler_method == 'exponential':
        return torch.optim.lr_scheduler.ExponentialLR(optimizer, gamma=0.95)