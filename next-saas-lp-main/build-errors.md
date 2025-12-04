PS E:\Gemnar-com\next-saas-lp-main> npm run build

> next-saas@0.1.0 build
> next build

   ▲ Next.js 15.2.3
   - Environments: .env.local

   Creating an optimized production build ...
 ✓ Compiled successfully

Failed to compile.

./src/app/(auth)/login/page.tsx
190:18  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities

./src/app/(auth)/signup/brand/page.tsx
3:20  Warning: 'useEffect' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(auth)/signup/creator/page.tsx
3:20  Warning: 'useEffect' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/analytics/pages/page.tsx
3:20  Warning: 'Eye' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/brands/acme-corp/settings/page.tsx
3:10  Warning: 'Building2' is defined but never used.  @typescript-eslint/no-unused-vars
3:41  Warning: 'Globe' is defined but never used.  @typescript-eslint/no-unused-vars
3:48  Warning: 'Settings' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/brands/page.tsx
3:36  Warning: 'Globe' is defined but never used.  @typescript-eslint/no-unused-vars
3:43  Warning: 'Settings' is defined but never used.  @typescript-eslint/no-unused-vars
17:10  Warning: 'showEditOrgModal' is assigned a value but never used.  @typescript-eslint/no-unused-vars
80:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
88:9  Warning: 'handleSetDefault' is assigned a value but never used.  @typescript-eslint/no-unused-vars
93:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
113:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
152:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
175:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
189:9  Warning: 'handleUpdateOrganization' is assigned a value but never used.  @typescript-eslint/no-unused-vars
205:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
213:9  Warning: 'handleDeleteOrganization' is assigned a value but never used.  @typescript-eslint/no-unused-vars
223:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
870:59  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
870:80  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities

./src/app/(dashboard)/dashboard/brands/[slug]/analytics/page.tsx
3:81  Warning: 'Calendar' is defined but never used.  @typescript-eslint/no-unused-vars
7:10  Warning: 'twitterAPI' is defined but never used.  @typescript-eslint/no-unused-vars
8:10  Warning: 'brandsAPI' is defined but never used.  @typescript-eslint/no-unused-vars
23:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/app/(dashboard)/dashboard/brands/[slug]/instagram/page.tsx
30:11  Error: An interface declaring no members is equivalent to its supertype.  @typescript-eslint/no-empty-object-type
64:32  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
442:21  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
535:21  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/dashboard/brands/[slug]/page.tsx
27:6  Warning: React Hook useEffect has a missing dependency: 'fetchBrand'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/app/(dashboard)/dashboard/brands/[slug]/twitter/config/page.tsx
7:10  Warning: 'twitterAPI' is defined but never used.  @typescript-eslint/no-unused-vars
8:10  Warning: 'brandsAPI' is defined but never used.  @typescript-eslint/no-unused-vars
39:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
160:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
194:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
245:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
290:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
406:44  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
406:59  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
407:59  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
407:65  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities

./src/app/(dashboard)/dashboard/brands/[slug]/twitter/page.tsx
13:3  Warning: 'BarChart3' is defined but never used.  @typescript-eslint/no-unused-vars
15:3  Warning: 'RefreshCw' is defined but never used.  @typescript-eslint/no-unused-vars
69:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
132:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
140:36  Warning: 'tweetId' is defined but never used.  @typescript-eslint/no-unused-vars
145:32  Warning: 'tweetId' is defined but never used.  @typescript-eslint/no-unused-vars
199:72  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities

./src/app/(dashboard)/dashboard/chat/new/page.tsx
6:10  Warning: 'chatApi' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/chat/page.tsx
41:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
55:14  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars
77:6  Warning: React Hook useEffect has a missing dependency: 'setupWebSocket'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
83:14  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars
128:14  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars
159:9  Warning: 'formatTime' is assigned a value but never used.  @typescript-eslint/no-unused-vars     
236:23  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
236:23  Warning: img elements must have an alt prop, either with meaningful text, or an empty string for decorative images.  jsx-a11y/alt-text
263:17  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
263:17  Warning: img elements must have an alt prop, either with meaningful text, or an empty string for decorative images.  jsx-a11y/alt-text
290:33  Warning: 'i' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/crm/contacts/page.tsx
3:60  Warning: 'Tag' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/crm/deals/page.tsx
3:36  Warning: 'TrendingUp' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/instagram/connect/page.tsx
3:43  Warning: 'ExternalLink' is defined but never used.  @typescript-eslint/no-unused-vars
44:20  Warning: 'error' is defined but never used.  @typescript-eslint/no-unused-vars
84:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
101:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/(dashboard)/dashboard/instagram/queue/page.tsx
374:29  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
583:41  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/dashboard/organizations/page.tsx
3:40  Warning: 'Mail' is defined but never used.  @typescript-eslint/no-unused-vars
3:46  Warning: 'MoreHorizontal' is defined but never used.  @typescript-eslint/no-unused-vars
3:62  Warning: 'Edit2' is defined but never used.  @typescript-eslint/no-unused-vars
8:10  Warning: 'brandsAPI' is defined but never used.  @typescript-eslint/no-unused-vars
60:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
83:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
117:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
328:49  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
328:68  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities

./src/app/(dashboard)/dashboard/organizations/[id]/page.tsx
3:45  Warning: 'Edit2' is defined but never used.  @typescript-eslint/no-unused-vars
3:73  Warning: 'Trash2' is defined but never used.  @typescript-eslint/no-unused-vars
8:10  Warning: 'brandsAPI' is defined but never used.  @typescript-eslint/no-unused-vars
32:6  Warning: React Hook useEffect has a missing dependency: 'loadOrganizationData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
72:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
95:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
110:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/(dashboard)/dashboard/page.tsx
4:50  Warning: 'Image' is defined but never used.  @typescript-eslint/no-unused-vars
4:57  Warning: 'Grid3x3' is defined but never used.  @typescript-eslint/no-unused-vars
47:29  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities
47:36  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities

./src/app/(dashboard)/dashboard/profile/billing/page.tsx
173:14  Warning: 'error' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/profile/page.tsx
3:22  Warning: 'Lock' is defined but never used.  @typescript-eslint/no-unused-vars
3:34  Warning: 'Globe' is defined but never used.  @typescript-eslint/no-unused-vars
5:10  Warning: 'getCurrentUser' is defined but never used.  @typescript-eslint/no-unused-vars
6:23  Warning: 'UserType' is defined but never used.  @typescript-eslint/no-unused-vars
288:23  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
847:14  Warning: 'error' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/settings/page.tsx
147:21  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/dashboard/tasks/all/page.tsx
3:23  Warning: 'Filter' is defined but never used.  @typescript-eslint/no-unused-vars
16:10  Warning: 'getCurrentUser' is defined but never used.  @typescript-eslint/no-unused-vars
37:6  Warning: React Hook useEffect has a missing dependency: 'loadTasks'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
48:19  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
130:9  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/dashboard/tasks/create/page.tsx
16:10  Warning: 'getCurrentUser' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/tasks/page.tsx
211:9  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/dashboard/tasks/[id]/page.tsx
52:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/app/(dashboard)/dashboard/twitter/analytics/page.tsx
3:22  Warning: 'TrendingDown' is defined but never used.  @typescript-eslint/no-unused-vars
3:45  Warning: 'CheckCircle' is defined but never used.  @typescript-eslint/no-unused-vars
3:58  Warning: 'XCircle' is defined but never used.  @typescript-eslint/no-unused-vars
18:6  Warning: React Hook useEffect has a missing dependency: 'fetchAnalytics'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
25:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/(dashboard)/dashboard/twitter/config/page.tsx
3:10  Warning: 'Settings' is defined but never used.  @typescript-eslint/no-unused-vars
3:20  Warning: 'Save' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/twitter/history/page.tsx
3:49  Warning: 'Twitter' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/dashboard/twitter/queue/page.tsx
3:139  Warning: 'ImageIcon' is defined but never used.  @typescript-eslint/no-unused-vars
4:20  Warning: 'useMemo' is defined but never used.  @typescript-eslint/no-unused-vars
39:35  Warning: 'brandsLoading' is assigned a value but never used.  @typescript-eslint/no-unused-vars  
293:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
500:27  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/app/(dashboard)/feed/page.tsx
8:25  Warning: 'User' is defined but never used.  @typescript-eslint/no-unused-vars
8:58  Warning: 'X' is defined but never used.  @typescript-eslint/no-unused-vars
29:6  Warning: React Hook useEffect has a missing dependency: 'loadFeed'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/app/(dashboard)/flow-generator/page.tsx
9:10  Warning: 'TopLeft' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/(dashboard)/flow-generator/[slug]/page.tsx
8:10  Warning: 'TopRight' is defined but never used.  @typescript-eslint/no-unused-vars
9:10  Warning: 'WorkspaceSelector' is defined but never used.  @typescript-eslint/no-unused-vars        

./src/app/(dashboard)/layout.tsx
20:3  Warning: 'ChevronDown' is defined but never used.  @typescript-eslint/no-unused-vars
25:3  Warning: 'Briefcase' is defined but never used.  @typescript-eslint/no-unused-vars
40:10  Warning: 'orgDropdownOpen' is assigned a value but never used.  @typescript-eslint/no-unused-vars
40:27  Warning: 'setOrgDropdownOpen' is assigned a value but never used.  @typescript-eslint/no-unused-vars
42:40  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
43:10  Warning: 'brandsLoading' is assigned a value but never used.  @typescript-eslint/no-unused-vars  
396:10  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
453:9  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
454:40  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/actions/ai.ts
418:36  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
439:38  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
455:34  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
464:47  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
464:73  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/actions/project.ts
3:10  Warning: 'cookies' is defined but never used.  @typescript-eslint/no-unused-vars
10:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
11:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/actions/workspace.ts
10:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
11:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
32:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
32:35  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
74:3  Warning: 'userId' is defined but never used.  @typescript-eslint/no-unused-vars
185:3  Warning: 'userId' is defined but never used.  @typescript-eslint/no-unused-vars
209:49  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/app/auth/instagram/callback/page.tsx
6:10  Warning: 'CheckCircle' is defined but never used.  @typescript-eslint/no-unused-vars
6:23  Warning: 'AlertCircle' is defined but never used.  @typescript-eslint/no-unused-vars

./src/app/users/[id]/page.tsx
23:6  Warning: React Hook useEffect has a missing dependency: 'loadData'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
119:17  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/AnimatedGroup.tsx
5:28  Warning: 'HTMLMotionProps' is defined but never used.  @typescript-eslint/no-unused-vars
121:3  Warning: 'as' is assigned a value but never used.  @typescript-eslint/no-unused-vars
122:3  Warning: 'asChild' is assigned a value but never used.  @typescript-eslint/no-unused-vars        

./src/components/flow/canvas.tsx
18:3  Warning: 'Panel' is defined but never used.  @typescript-eslint/no-unused-vars
173:19  Warning: 'oldId' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/components/flow/nodes/audio-node.tsx
10:24  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/components/flow/nodes/image/primitive.tsx
41:13  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/flow/nodes/image/transform.tsx
62:13  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/flow/nodes/text/primitive.tsx
7:43  Warning: 'type' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow/nodes/text/transform.tsx
10:43  Warning: 'type' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow/nodes/text-node.tsx
4:30  Warning: 'useReactFlow' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow/nodes/video-node.tsx
10:24  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/components/flow-components/canvas.tsx
46:20  Warning: 'updateProject' is assigned a value but never used.  @typescript-eslint/no-unused-vars  
50:5  Warning: 'onConnectStart' is assigned a value but never used.  @typescript-eslint/no-unused-vars  
51:5  Warning: 'onConnectEnd' is assigned a value but never used.  @typescript-eslint/no-unused-vars    
73:6  Warning: React Hook useEffect has a missing dependency: 'project.content'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
100:54  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
218:19  Warning: 'oldId' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/controls.tsx
5:10  Warning: 'ThemeSwitcher' is defined but never used.  @typescript-eslint/no-unused-vars
7:44  Warning: 'MousePointer2' is defined but never used.  @typescript-eslint/no-unused-vars
7:59  Warning: 'Hand' is defined but never used.  @typescript-eslint/no-unused-vars
55:54  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/components/flow-components/nodes/audio/transform.tsx
36:7  Warning: '_' is defined but never used.  @typescript-eslint/no-unused-vars
80:9  Warning: 'instructions' is assigned a value but never used.  @typescript-eslint/no-unused-vars    

./src/components/flow-components/nodes/audio/voice-selector.tsx
33:11  Warning: 'plan' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/nodes/code/transform.tsx
38:7  Warning: '_' is defined but never used.  @typescript-eslint/no-unused-vars
133:6  Warning: React Hook useCallback has a missing dependency: 'language'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/components/flow-components/nodes/image/transform.tsx
41:7  Warning: '_' is defined but never used.  @typescript-eslint/no-unused-vars
68:9  Warning: The 'allReferenceImages' array makes the dependencies of useCallback Hook (at line 174) change on every render. To fix this, wrap the initialization of 'allReferenceImages' in its own useMemo() Hook.  react-hooks/exhaustive-deps

./src/components/flow-components/nodes/text/transform.tsx
49:7  Warning: '_' is defined but never used.  @typescript-eslint/no-unused-vars
186:6  Warning: React Hook useCallback has a missing dependency: 'analytics'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/components/flow-components/nodes/video/transform.tsx
4:10  Warning: 'Skeleton' is defined but never used.  @typescript-eslint/no-unused-vars
36:7  Warning: '_' is defined but never used.  @typescript-eslint/no-unused-vars
71:34  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/components/flow-components/profile.tsx
10:10  Warning: 'uploadFile' is defined but never used.  @typescript-eslint/no-unused-vars
32:17  Warning: 'setImage' is assigned a value but never used.  @typescript-eslint/no-unused-vars       
178:9  Warning: The attribute aria-disabled is not supported by the role form. This role is implicit on the element form.  jsx-a11y/role-supports-aria-props

./src/components/flow-components/project-selector.tsx
197:13  Warning: The attribute aria-disabled is not supported by the role form. This role is implicit on the element form.  jsx-a11y/role-supports-aria-props

./src/components/flow-components/project-settings.tsx
99:49  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities
101:9  Warning: The attribute aria-disabled is not supported by the role form. This role is implicit on the element form.  jsx-a11y/role-supports-aria-props

./src/components/flow-components/publish-dialog.tsx
14:10  Warning: 'Input' is defined but never used.  @typescript-eslint/no-unused-vars
17:30  Warning: 'ImageIcon' is defined but never used.  @typescript-eslint/no-unused-vars
19:26  Warning: 'WorkspaceMedia' is defined but never used.  @typescript-eslint/no-unused-vars
67:13  Warning: 'publishedWorkspace' is assigned a value but never used.  @typescript-eslint/no-unused-vars
216:23  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
245:25  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/flow-components/top-left.tsx
8:14  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/components/flow-components/ui/kibo-ui/ai/branch.tsx
86:9  Warning: The 'childrenArray' conditional could make the dependencies of useEffect Hook (at line 93) change on every render. To fix this, wrap the initialization of 'childrenArray' in its own useMemo() Hook.  react-hooks/exhaustive-deps

./src/components/flow-components/ui/kibo-ui/ai/reasoning.tsx
120:5  Warning: 'title' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/ui/kibo-ui/ai/response.tsx
32:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
37:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
42:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
47:14  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
52:9  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
62:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
70:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
78:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
83:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
88:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
96:10  Warning: 'node' is defined but never used.  @typescript-eslint/no-unused-vars
171:27  Error: Component definition is missing display name  react/display-name

./src/components/flow-components/ui/kibo-ui/ai/source.tsx
28:3  Warning: 'className' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/ui/kibo-ui/ai/tool.tsx
28:3  Warning: 'status' is assigned a value but never used.  @typescript-eslint/no-unused-vars
70:3  Warning: 'description' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/ui/kibo-ui/code-block/index.tsx
387:3  Warning: 'className' is defined but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/ui/kibo-ui/combobox/index.tsx
212:11  Warning: 'value' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/components/flow-components/workspace-selector.tsx
99:5  Warning: React Hook useCallback has an unnecessary dependency: 'user'. Either exclude it or remove the dependency array.  react-hooks/exhaustive-deps
152:23  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
325:13  Warning: The attribute aria-disabled is not supported by the role form. This role is implicit on the element form.  jsx-a11y/role-supports-aria-props
351:13  Warning: The attribute aria-disabled is not supported by the role form. This role is implicit on the element form.  jsx-a11y/role-supports-aria-props

./src/components/followCursor.tsx
52:9  Warning: 'cursorRef' is assigned a value but never used.  @typescript-eslint/no-unused-vars       

./src/components/ImageGallery.tsx
18:3  Warning: 'maxSelection' is assigned a value but never used.  @typescript-eslint/no-unused-vars    
93:14  Warning: 'error' is defined but never used.  @typescript-eslint/no-unused-vars
184:17  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
307:11  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/InstagramSetupGuide.tsx
37:27  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
37:38  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
37:42  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
37:51  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
37:55  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
37:60  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
38:43  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
38:60  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
39:25  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
39:49  Error: `"` can be escaped with `&quot;`, `&ldquo;`, `&#34;`, `&rdquo;`.  react/no-unescaped-entities
129:18  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities

./src/components/MediaGallery.tsx
19:3  Warning: 'Play' is defined but never used.  @typescript-eslint/no-unused-vars
20:3  Warning: 'Pause' is defined but never used.  @typescript-eslint/no-unused-vars
21:3  Warning: 'Volume2' is defined but never used.  @typescript-eslint/no-unused-vars
22:3  Warning: 'VolumeX' is defined but never used.  @typescript-eslint/no-unused-vars
24:3  Warning: 'Calendar' is defined but never used.  @typescript-eslint/no-unused-vars
26:3  Warning: 'MoreHorizontal' is defined but never used.  @typescript-eslint/no-unused-vars
44:3  Warning: 'maxSelection' is assigned a value but never used.  @typescript-eslint/no-unused-vars    
73:9  Warning: 'uniqueFormats' is assigned a value but never used.  @typescript-eslint/no-unused-vars   
141:14  Warning: 'error' is defined but never used.  @typescript-eslint/no-unused-vars
305:71  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
319:70  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
509:11  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
747:17  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/MediaViewer.tsx
75:6  Warning: React Hook useEffect has a missing dependency: 'togglePlay'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
235:17  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/components/WorkspaceMediaGallery.tsx
9:3  Warning: 'Download' is defined but never used.  @typescript-eslint/no-unused-vars
10:3  Warning: 'Trash2' is defined but never used.  @typescript-eslint/no-unused-vars
11:3  Warning: 'Upload' is defined but never used.  @typescript-eslint/no-unused-vars
15:3  Warning: 'X' is defined but never used.  @typescript-eslint/no-unused-vars
18:3  Warning: 'Calendar' is defined but never used.  @typescript-eslint/no-unused-vars
39:3  Warning: 'showUpload' is assigned a value but never used.  @typescript-eslint/no-unused-vars      
45:5  Warning: 'workspaces' is assigned a value but never used.  @typescript-eslint/no-unused-vars      
60:10  Warning: 'showUploadModal' is assigned a value but never used.  @typescript-eslint/no-unused-vars
60:27  Warning: 'setShowUploadModal' is assigned a value but never used.  @typescript-eslint/no-unused-vars
102:9  Warning: 'getFileIcon' is assigned a value but never used.  @typescript-eslint/no-unused-vars    
108:9  Warning: 'formatFileSize' is assigned a value but never used.  @typescript-eslint/no-unused-vars 
115:9  Warning: 'formatDate' is assigned a value but never used.  @typescript-eslint/no-unused-vars     
196:68  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
304:11  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
314:15  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
403:11  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
413:15  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

./src/hooks/use-analytics.ts
4:70  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/hooks/use-brands.ts
41:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
60:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
81:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/hooks/use-instagram.ts
25:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
128:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
151:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
199:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
212:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
224:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
236:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
295:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
307:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/hooks/use-media-gallery.ts
206:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
330:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
364:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
418:6  Warning: React Hook useEffect has a missing dependency: 'allMedia.length'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps

./src/hooks/use-twitter.ts
22:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
47:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
72:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
88:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
125:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
147:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
160:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
175:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
194:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
220:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/hooks/use-user.ts
4:34  Warning: 'DjangoUser' is defined but never used.  @typescript-eslint/no-unused-vars
19:10  Warning: 'loading' is assigned a value but never used.  @typescript-eslint/no-unused-vars        

./src/hooks/use-workspace-media.ts
34:10  Warning: 'storageFilter' is assigned a value but never used.  @typescript-eslint/no-unused-vars  
34:25  Warning: 'setStorageFilter' is assigned a value but never used.  @typescript-eslint/no-unused-vars
96:60  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
170:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
223:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
238:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
359:37  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
365:15  Warning: 'key' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/lib/api/audio-generation.ts
213:16  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars

./src/lib/api/image-generation.ts
142:16  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars
264:16  Warning: 'e' is defined but never used.  @typescript-eslint/no-unused-vars

./src/lib/api/organizations.ts
135:55  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/api/twitter.ts
277:21  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/api/video-generation.ts
59:10  Warning: 'dataUrlToFile' is defined but never used.  @typescript-eslint/no-unused-vars
83:5  Warning: 'cookieHeader' is assigned a value but never used.  @typescript-eslint/no-unused-vars    
151:5  Warning: 'cookieHeader' is assigned a value but never used.  @typescript-eslint/no-unused-vars   

./src/lib/models/text.ts
8:11  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/models/transcription.ts
1:15  Warning: 'TersaModel' is defined but never used.  @typescript-eslint/no-unused-vars

./src/lib/models/video.ts
1:15  Warning: 'TersaModel' is defined but never used.  @typescript-eslint/no-unused-vars

./src/lib/models/vision.ts
1:15  Warning: 'TersaModel' is defined but never used.  @typescript-eslint/no-unused-vars

./src/lib/providers.ts
8:9  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
95:10  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/upload.ts
9:3  Warning: 'folder' is assigned a value but never used.  @typescript-eslint/no-unused-vars

./src/lib/workspace-api.ts
25:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
26:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
76:37  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
121:44  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
121:58  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
203:51  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
227:51  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
250:51  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
314:51  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
336:37  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
341:39  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
362:51  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/xyflow-helpers.ts
13:44  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
27:52  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/lib/xyflow.ts
22:33  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
26:33  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
40:33  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
44:33  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

./src/providers/flow-provider.tsx
4:15  Warning: 'Node' is defined but never used.  @typescript-eslint/no-unused-vars
4:21  Warning: 'Edge' is defined but never used.  @typescript-eslint/no-unused-vars

./src/providers/project-provider.tsx
11:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any
12:12  Warning: Unexpected any. Specify a different type.  @typescript-eslint/no-explicit-any

info  - Need to disable some ESLint rules? Learn more here: https://nextjs.org/docs/app/api-reference/config/eslint#disabling-rules
PS E:\Gemnar-com\next-saas-lp-main>
