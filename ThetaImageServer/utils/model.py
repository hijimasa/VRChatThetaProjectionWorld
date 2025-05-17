import os
import sys

import torch

from baseline_models.UniFuse.networks import UniFuse
from utils.metric import ScaleAndShiftInvariantLoss


def get_model(model_name, device, pretrained_dict=None, model_dict=None):
    if model_name.upper() == 'UNIFUSE':
        model = UniFuse(**model_dict)
    else:
        raise NotImplementedError(f"{model_name} not implemented")
    model.to(device)

    if pretrained_dict:
        model_dict = model.state_dict()
        # some model trained with nn.DataParallel
        pretrained_keys = [k for k in pretrained_dict.keys() if k.startswith('module.')]
        if len(pretrained_keys) > 0:
            # trained with DataParallel, remove module from pretrained dict
            pretrained_dict = {k[7:]: v for k, v in pretrained_dict.items() if k[7:] in model_dict}
        else:
            pretrained_dict = {k: v for k, v in pretrained_dict.items() if k in model_dict}

        # load
        model_dict.update(pretrained_dict)
        model.load_state_dict(model_dict)

    if torch.cuda.device_count() > 1:
        model = torch.nn.DataParallel(model)

    model.get_loss = ScaleAndShiftInvariantLoss()

    return model


def save_model(model, optim, args):
    """Save model to .pth file."""
    save_path = os.path.join(args.save_folder, f"ckpt_{args.cur_epoch}.pth")
    to_save = dict()
    if hasattr(model, 'module'):
        # nn.DataParallel
        to_save['model'] = model.module.state_dict()
    else:
        to_save['model'] = model.state_dict()

    to_save['optim'] = optim.state_dict()
    to_save['settings'] = args
    torch.save(to_save, save_path)
