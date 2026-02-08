import { AuthGuard } from "@/components/layout/auth-guard";

import { ChatContainer } from "@/features/chat/chat-container";

export function ChatPage(): preact.JSX.Element {
  return (
    <AuthGuard permission="chat.use">
      <div class="-mx-6 -mt-6 -mb-6 h-[calc(100vh-3.5rem)]">
        <ChatContainer />
      </div>
    </AuthGuard>
  );
}
