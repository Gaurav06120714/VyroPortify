import { NextResponse } from "next/server";
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/login(.*)",
  "/register(.*)",
  "/portfolio/(.*)",
  "/pricing(.*)",
  "/templates(.*)",
  "/api/webhook(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isPublicRoute(req)) return;

  // Bare `auth.protect()` returns 404 for unauthenticated visitors, which made
  // /dashboard/* (incl. /dashboard/settings/billing) look broken instead of
  // bouncing the user to login. Redirect explicitly to /login with a
  // redirect_url so Clerk returns them to the originally requested page.
  const { userId } = await auth();
  if (!userId) {
    const url = req.nextUrl.clone();
    const target = url.pathname + url.search;
    url.pathname = "/login";
    url.searchParams.set("redirect_url", target);
    return NextResponse.redirect(url);
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
