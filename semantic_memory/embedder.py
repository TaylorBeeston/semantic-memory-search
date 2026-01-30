"""Embedding generator using local EmbeddingGemma model."""

import torch
import numpy as np
from pathlib import Path
from typing import List, Union


class Embedder:
    """Generate embeddings using local EmbeddingGemma 300m model."""
    
    def __init__(self, model_path: Union[str, Path] = None):
        """Initialize the embedder.
        
        Args:
            model_path: Path to the safetensors model directory.
                       Defaults to /home/computer/models/embeddinggemma-300m
        """
        if model_path is None:
            model_path = "/home/computer/models/embeddinggemma-300m"
        
        self.model_path = Path(model_path)
        self._model = None
        self._tokenizer = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._embedding_dim = 768  # EmbeddingGemma-300m output dimension
        
    def _load(self):
        """Lazy load the model and tokenizer."""
        if self._model is not None:
            return
            
        from transformers import AutoModel, AutoTokenizer
        
        print(f"Loading EmbeddingGemma from {self.model_path}...")
        print(f"Using device: {self._device}")
        
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self._model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16 if self._device == "cuda" else torch.float32
        ).to(self._device)
        self._model.eval()
        
    def encode(self, texts: Union[str, List[str]], batch_size: int = 8) -> np.ndarray:
        """Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            Numpy array of embeddings (shape: [n_texts, 768])
        """
        self._load()
        
        if isinstance(texts, str):
            texts = [texts]
            
        all_embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Tokenize
                encoded = self._tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(self._device)
                
                # Generate embeddings (mean pooling)
                outputs = self._model(**encoded)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                
                # Normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
                all_embeddings.append(embeddings.cpu().numpy())
        
        return np.vstack(all_embeddings)
    
    @property
    def dim(self) -> int:
        """Return embedding dimension."""
        return self._embedding_dim
