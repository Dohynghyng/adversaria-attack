import torch
import torch.nn as nn

import numpy as np

mean, std = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
mean, std = torch.Tensor(mean).cuda(), torch.Tensor(std).cuda()

def ifgsm(model, X, config):
    X_pert = X.clone()
    X = X.clone()
    X_pert.requires_grad = True
    for i in range(config['n_iter']):
        output_perturbed = model(X_pert)
        y_used = torch.zeros_like(output_perturbed) - config['delta']
        y_used = torch.FloatTensor(y_used.cpu()).cuda()
        loss = nn.MSELoss()(output_perturbed, y_used)
        loss.backward()
        pert = 1 * config['lr'] * X_pert.grad.detach().sign()
        X_pert = update_adv(X, X_pert, pert, config['eps'])
        X_pert.requires_grad = True
    adv_ex = generate_x_adv(X_pert.clone().detach(),config["mean"],config['std'])
    return adv_ex

def traditional_ifgsm(model, X, y, config):
    X_pert = X.clone()
    X = X.clone()
    X_pert.requires_grad = True
    for i in range(config['n_iter']):
        output_perturbed = model(X_pert)
        if isinstance(output_perturbed, dict):
            output_perturbed = output_perturbed['out']
        loss = nn.MSELoss()(output_perturbed, y)
        loss.backward()
        pert = 1 * config['lr'] * X_pert.grad.detach().sign()
        X_pert = update_adv(X, X_pert, pert, config['eps'])
        X_pert.requires_grad = True
    adv_ex = generate_x_adv(X_pert.clone().detach(),config["mean"],config['std'])
    return adv_ex

def update_adv(X, X_pert, pert, epsilon):
    X = X.clone().detach()
    X_pert = X_pert.clone().detach()
    X_pert = X_pert + pert
    noise = X_pert - X
    noise = torch.permute(noise,(0,2,3,1))
    noise = torch.clamp(noise, -epsilon/std, epsilon/std)
    noise = torch.permute(noise,(0,3,1,2))
    X_pert = X + noise

    X_pert = torch.permute(X_pert,(0,2,3,1))
    X_pert = torch.clamp(X_pert, min=-mean/std, max=(1-mean)/std)
    X_pert = torch.permute(X_pert,(0,3,1,2))
    return X_pert.clone().detach()

def generate_x_adv(x_adv, mean, std):
    x_adv = x_adv.detach()
    x_adv = normalize_inverse(x_adv, mean, std)
    x_adv_img = np.transpose(x_adv.detach().cpu().numpy()[0], (1,2,0))
    x_adv_img = np.asarray(np.round(x_adv_img,0),dtype=np.uint8)
    return x_adv_img

def normalize_inverse(img, mean, std):
    for c, (mean_c, std_c) in enumerate(zip(mean, std)):
        img[:,c,:,:] *= std_c
        img[:,c,:,:] += mean_c
    img *= 255
    return img
