// Mock database - no actual database connection
export const database = {
  query: {
    projects: {
      findMany: async () => [],
      findFirst: async () => null,
    },
  },
  select: () => ({
    from: () => ({
      where: () => ({
        limit: () => Promise.resolve([]),
      }),
    }),
  }),
};
