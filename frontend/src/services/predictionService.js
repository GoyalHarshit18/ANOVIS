import { apiService } from './apiService';

export const predictionService = {
  getPrediction: async (componentId) => {
    return await apiService.getComponent(componentId);
  }
};
