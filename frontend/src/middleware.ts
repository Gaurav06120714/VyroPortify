import { NextResponse } from "next/server";
import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/login(.*)",
  "/register(.*)",
  "/signup(.*)",            
  "/portfolio/(.*)",
  "/pricing(.*)",
  "/templates(.*)",
  "/api/webhook(.*)",
  
  "/sitemap.xml",
  "/robots.txt",
  "/manifest.webmanifest",
  "/favicon.ico",
  "/_next/(.*)",            
]);

export default clerkMiddleware(async (auth, req) => {
  if (isPublicRoute(req)) return;

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
