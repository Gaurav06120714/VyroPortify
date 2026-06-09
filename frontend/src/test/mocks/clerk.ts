import { vi } from "vitest";

export const mockGetToken = vi.fn().mockResolvedValue("mock-bearer-token");
export const mockUseAuth = vi.fn().mockReturnValue({
  isSignedIn: true,
  isLoaded: true,
  getToken: mockGetToken,
});
export const mockUseUser = vi.fn().mockReturnValue({
  isLoaded: true,
  isSignedIn: true,
  user: {
    id: "user_test_001",
    firstName: "Test",
    lastName: "User",
    emailAddresses: [{ emailAddress: "test@example.com" }],
    imageUrl: "https://example.com/avatar.jpg",
  },
});

export const clerkMocks = {
  useAuth: mockUseAuth,
  useUser: mockUseUser,
  ClerkProvider: ({ children }: { children: React.ReactNode }) => children,
  SignIn: () => null,
  SignUp: () => null,
};
