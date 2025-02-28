from datasets import load_dataset
import h5py
import torch
import matplotlib.pyplot as plt
import einx
import numpy as np
import open_clip
from PIL import Image
from torchvision import transforms
import os
from tqdm import tqdm


MODEL_NAME = "ViT-L-14"
PRETRAINED_DATASET = "openai"  # Use "laion2b_s32b_b82k" for OpenCLIP versions

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess, tokenizer = open_clip.create_model_and_transforms(MODEL_NAME, pretrained=PRETRAINED_DATASET)
model.to(device)
model.eval()

alljoined_folder = "../data/alljoined1"

if not os.path.isdir(alljoined_folder):
	os.makedirs(alljoined_folder)

ds = load_dataset("Alljoined/05_125")

subset_id = np.unique(ds["train"]["73k_id"])

h5_path = "../data/alljoined1/coco_images_224_float16.hdf5"

imgs = []
indices = []
embeds = []

with h5py.File(h5_path,'r') as source_hdf5:
	for i in tqdm(subset_id):
		img = torch.Tensor(source_hdf5['images'][i])
		with torch.no_grad():
			torch_img = einx.rearrange("c h w -> 1 c h w",img.to(torch.float32))
			embed = model.encode_image(torch_img.to(device))
		indices.append(i)
		imgs.append(img)
		embeds.append(embed.cpu())

dset = {"idx":indices,"imgs":torch.stack(imgs),"embeds":torch.stack(embeds)}

torch.save(dset,os.path.join(alljoined_folder,"nsd_ms_coco.pt"))