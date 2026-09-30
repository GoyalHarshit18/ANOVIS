import { apiService } from './apiService';

export const riskFusionService = {
  getRiskFusion: async (componentId) => {
    return await apiService.getComponent(componentId);
  }
};
