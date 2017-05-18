"""Optimizer."""
import numpy as np
from time import time


class Optimizer:
    """Ground state optimizer."""

    def __init__(self, model, sampler, system):
        """Initialise."""
        self.model = model
        self.sampler = sampler
        self.system = system

    def optimize(self, iterations, num_samples):
        """Perform optimization."""
        for it in range(iterations):
            start = time()
            samples = self.sampler.sample(num_samples)
            time_sample, start = time()-start, time()
            E = self.system.local_energy(samples)
            O = self.model.backward(samples)
            O_conj = np.conj(O)

            F = np.dot(O_conj.T, E) / num_samples
            F -= np.mean(E, axis=0)*np.mean(O_conj, axis=0)
            time_model, start = time()-start, time()
            delta = -1 * F

            self.model.set_params(self.model.params + delta)
            time_solve, start = time()-start, time()

            print(("Iteration %d/%d, E=%f (%.2f), w=%.2E delta=%.2E "
                   "(%.2fs, %.2fs, %.2fs)") %
                  (it, iterations, np.real(np.mean(E)),
                   np.std(E)/np.sqrt(num_samples),
                   np.mean(np.absolute(self.model.params)),
                   np.mean(np.absolute(delta)),
                   time_sample, time_model, time_solve))


class TFOptimizer:
    """Ground state optimizer."""

    def __init__(self, model, sampler, system):
        """Initialise."""
        self.model = model
        self.sampler = sampler
        self.system = system

    def optimize(self, iterations, train_samples,
                 eval_freq=None, eval_samples=None):
        """Perform optimization."""
        for it in range(iterations):
            start = time()
            samples = self.sampler.sample(train_samples)
            time_sample, start = time()-start, time()
            E = self.model.batch(self.system.local_energy, samples,
                                 self.model.ENERGY_BATCH_SIZE)
            time_energy, start = time()-start, time()
            self.model.optimize(self.model.unpad(samples, 'half'), E)
            time_optimize, start = time()-start, time()

            print(("Iteration %d/%d, E=%f (%.2E), "
                   "(%.2fs, %.2fs, %.2fs)") %
                  (it, iterations, np.real(np.mean(E)),
                   np.std(E)/np.sqrt(train_samples),
                   time_sample, time_energy, time_optimize))

            if eval_freq is not None and it % eval_freq == 0:
                start = time()
                samples = self.sampler.sample(eval_samples)
                time_sample, start = time()-start, time()
                E = self.system.local_energy(samples)
                time_energy = time()-start

                print(("Evaluation, E=%f (%.2E), "
                       "(%.2fs, %.2fs)") %
                      (np.real(np.mean(E)), np.std(E)/np.sqrt(eval_samples),
                       time_sample, time_energy))
