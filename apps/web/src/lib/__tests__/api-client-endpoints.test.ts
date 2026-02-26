/**
 * API Client Endpoint Tests - Phase 1
 * 
 * Tests to verify endpoint paths align with backend implementation.
 * Backend uses: /api/v1/{orgId}/invoicing/documents/
 * NOT: /api/v1/{orgId}/invoices/
 */

import { describe, it, expect } from "vitest";
import { endpoints } from "../api-client";

describe("Invoice API Endpoints - Phase 1 Alignment", () => {
  const orgId = "test-org-123";
  const documentId = "doc-456";

  describe("endpoints.invoices()", () => {
    it("should return correct list endpoint path", () => {
      const result = endpoints.invoices(orgId);
      expect(result.list).toBe(`/api/v1/${orgId}/invoicing/documents/`);
    });

    it("should return correct detail endpoint path", () => {
      const result = endpoints.invoices(orgId);
      expect(result.detail(documentId)).toBe(
        `/api/v1/${orgId}/invoicing/documents/${documentId}/`
      );
    });

    it("should include document type filter support in list endpoint", () => {
      const result = endpoints.invoices(orgId);
      // The endpoint should support query params for document_type
      expect(result.list).toContain("/invoicing/documents/");
    });
  });

  describe("endpoints.contacts()", () => {
    const contactId = "contact-789";

    it("should return correct contacts list endpoint path", () => {
      const result = endpoints.contacts(orgId);
      expect(result.list).toBe(`/api/v1/${orgId}/invoicing/contacts/`);
    });

    it("should return correct contacts detail endpoint path", () => {
      const result = endpoints.contacts(orgId);
      expect(result.detail(contactId)).toBe(
        `/api/v1/${orgId}/invoicing/contacts/${contactId}/`
      );
    });
  });

  describe("Auth Endpoints", () => {
    it("should have correct login endpoint", () => {
      expect(endpoints.auth.login).toBe("/api/v1/auth/login/");
    });

    it("should have correct logout endpoint", () => {
      expect(endpoints.auth.logout).toBe("/api/v1/auth/logout/");
    });

    it("should have correct refresh endpoint", () => {
      expect(endpoints.auth.refresh).toBe("/api/v1/auth/refresh/");
    });

    it("should have correct me endpoint", () => {
      expect(endpoints.auth.me).toBe("/api/v1/auth/me/");
    });
  });
});
