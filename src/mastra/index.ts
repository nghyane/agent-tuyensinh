import { ConsoleLogger } from '@mastra/core/logger';
import { Mastra } from '@mastra/core/mastra';

import { admissionsAgent, metadataAgent } from '@/mastra/agents';

export const mastra = new Mastra({
  agents: { admissionsAgent, metadataAgent },
  
  logger: new ConsoleLogger(),
});
