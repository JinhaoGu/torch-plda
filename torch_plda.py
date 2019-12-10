import torch
import plda_func
import warnings


# TODO add PLDA Scoring for speech processing applications
class PLDA:
    """
    Probabilistic Linear Discriminant Analysis as described in:
        https://ravisoji.com/assets/papers/ioffe2006probabilistic.pdf
    """

    def __init__(self, latent_space_dim: int = None):
        """
        :param latent_space_dim: the number of dimensions in the latent space.
            This value might be overriden if not enough features are discoverded by the algorithm
        """
        self.latent_dim = latent_space_dim
        self.m, self.inv_A, self.Psi, self.latent_idx = None, None, None, None

    def fit(self, X, y):
        """
        Fits the PLDA model according to the algorithm described in:
            https://ravisoji.com/assets/papers/ioffe2006probabilistic.pdf
            (Figure 2, p537)
        :param X: a Float matrix of training vectors of size (N, d), where d is the vector dimension
        :param y: a Long vector of class labels
        """
        with torch.no_grad():
            self.m, self.inv_A, self.Psi = plda_func.plda(X, y)
            # Update latent space dimension if not specified or not possible
            n_important_feats = self.Psi.nonzero().sum().item()
            if self.latent_dim is not None and n_important_feats < self.latent_dim:
                warnings.warn(f"PLDA identified a latent space dimension of {n_important_feats}, "
                              f"but the user specified {self.latent_dim}. "
                              f"Setting latent space dimension to {n_important_feats}")
                self.latent_dim = n_important_feats
            elif self.latent_dim is None:
                self.latent_dim = n_important_feats
            # Get the ids of the `latent_dim` most important features detected by the model
            self.latent_idx = torch.argsort(self.Psi, descending=True)[:self.latent_dim].sort()[0]

    def __call__(self, batch):
        """
        Encode a batch of vector examples using the previously fit model
        :param batch: a Float matrix of vectors of size (n, d), where d is the vector dimension
        :return: an encoding of the batch using only the detected important features
        """
        with torch.no_grad():
            if self.latent_idx is None:
                raise AssertionError('You need to call `fit` before applying the model')
            # Transposing x because PyTorch uses row vectors by default
            u = torch.matmul(self.inv_A, batch.transpose(0, 1) - self.m)
            # Select only valuable dimensions for the latent space
            return torch.index_select(u, 1, self.latent_idx)