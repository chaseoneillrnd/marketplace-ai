--
-- PostgreSQL database dump
--

\restrict 9aCQnXqthQSb5EdIy05oZdpH1Mh3VVUqRz2yEoqbQ4UlGS6mnVzXaywQdx3Ui4P

-- Dumped from database version 16.12
-- Dumped by pg_dump version 16.12

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: audit_log_immutable(); Type: FUNCTION; Schema: public; Owner: skillhub
--

CREATE FUNCTION public.audit_log_immutable() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are not allowed';
        END;
        $$;


ALTER FUNCTION public.audit_log_immutable() OWNER TO skillhub;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO skillhub;

--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.audit_log (
    id uuid NOT NULL,
    event_type character varying(100) NOT NULL,
    actor_id uuid,
    target_type character varying(50),
    target_id character varying(255),
    metadata json,
    ip_address character varying(45),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.audit_log OWNER TO skillhub;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.categories (
    slug character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    sort_order integer NOT NULL
);


ALTER TABLE public.categories OWNER TO skillhub;

--
-- Name: comment_votes; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.comment_votes (
    comment_id uuid NOT NULL,
    user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.comment_votes OWNER TO skillhub;

--
-- Name: comments; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.comments (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    user_id uuid NOT NULL,
    body text NOT NULL,
    upvote_count integer NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.comments OWNER TO skillhub;

--
-- Name: division_access_requests; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.division_access_requests (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    requested_by uuid NOT NULL,
    user_division character varying(100) NOT NULL,
    reason text NOT NULL,
    status character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.division_access_requests OWNER TO skillhub;

--
-- Name: divisions; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.divisions (
    slug character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    color character varying(7)
);


ALTER TABLE public.divisions OWNER TO skillhub;

--
-- Name: favorites; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.favorites (
    user_id uuid NOT NULL,
    skill_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.favorites OWNER TO skillhub;

--
-- Name: feature_flags; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.feature_flags (
    key character varying(100) NOT NULL,
    enabled boolean NOT NULL,
    description text,
    division_overrides json
);


ALTER TABLE public.feature_flags OWNER TO skillhub;

--
-- Name: follows; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.follows (
    follower_id uuid NOT NULL,
    followed_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.follows OWNER TO skillhub;

--
-- Name: forks; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.forks (
    id uuid NOT NULL,
    original_skill_id uuid NOT NULL,
    forked_skill_id uuid NOT NULL,
    forked_by uuid NOT NULL,
    upstream_version_at_fork character varying(50) NOT NULL,
    forked_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.forks OWNER TO skillhub;

--
-- Name: installs; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.installs (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    user_id uuid NOT NULL,
    version character varying(50) NOT NULL,
    method character varying(20) NOT NULL,
    installed_at timestamp with time zone DEFAULT now() NOT NULL,
    uninstalled_at timestamp with time zone
);


ALTER TABLE public.installs OWNER TO skillhub;

--
-- Name: oauth_sessions; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.oauth_sessions (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    provider character varying(50) NOT NULL,
    access_token_hash character varying(128) NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.oauth_sessions OWNER TO skillhub;

--
-- Name: replies; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.replies (
    id uuid NOT NULL,
    comment_id uuid NOT NULL,
    user_id uuid NOT NULL,
    body text NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.replies OWNER TO skillhub;

--
-- Name: review_votes; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.review_votes (
    review_id uuid NOT NULL,
    user_id uuid NOT NULL,
    vote character varying(10) NOT NULL
);


ALTER TABLE public.review_votes OWNER TO skillhub;

--
-- Name: reviews; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.reviews (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    user_id uuid NOT NULL,
    rating integer NOT NULL,
    body text NOT NULL,
    helpful_count integer NOT NULL,
    unhelpful_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.reviews OWNER TO skillhub;

--
-- Name: skill_divisions; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.skill_divisions (
    skill_id uuid NOT NULL,
    division_slug character varying(100) NOT NULL
);


ALTER TABLE public.skill_divisions OWNER TO skillhub;

--
-- Name: skill_tags; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.skill_tags (
    skill_id uuid NOT NULL,
    tag character varying(100) NOT NULL
);


ALTER TABLE public.skill_tags OWNER TO skillhub;

--
-- Name: skill_versions; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.skill_versions (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    version character varying(50) NOT NULL,
    content text NOT NULL,
    frontmatter json,
    changelog text,
    content_hash character varying(64) NOT NULL,
    published_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.skill_versions OWNER TO skillhub;

--
-- Name: skills; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.skills (
    id uuid NOT NULL,
    slug character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    short_desc character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    author_id uuid NOT NULL,
    author_type character varying(20) NOT NULL,
    current_version character varying(50) NOT NULL,
    install_method character varying(20) NOT NULL,
    data_sensitivity character varying(10) NOT NULL,
    external_calls boolean NOT NULL,
    verified boolean NOT NULL,
    featured boolean NOT NULL,
    featured_order integer,
    status character varying(20) NOT NULL,
    install_count integer NOT NULL,
    fork_count integer NOT NULL,
    favorite_count integer NOT NULL,
    view_count integer NOT NULL,
    review_count integer NOT NULL,
    avg_rating numeric(3,2) NOT NULL,
    trending_score numeric(10,4) NOT NULL,
    published_at timestamp with time zone,
    deprecated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.skills OWNER TO skillhub;

--
-- Name: submission_gate_results; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.submission_gate_results (
    id uuid NOT NULL,
    submission_id uuid NOT NULL,
    gate integer NOT NULL,
    result character varying(10) NOT NULL,
    findings json,
    score integer,
    reviewer_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.submission_gate_results OWNER TO skillhub;

--
-- Name: submissions; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.submissions (
    id uuid NOT NULL,
    display_id character varying(10) NOT NULL,
    skill_id uuid,
    submitted_by uuid NOT NULL,
    name character varying(255) NOT NULL,
    short_desc character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    content text NOT NULL,
    declared_divisions json NOT NULL,
    division_justification text NOT NULL,
    status character varying(30) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.submissions OWNER TO skillhub;

--
-- Name: trigger_phrases; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.trigger_phrases (
    id uuid NOT NULL,
    skill_id uuid NOT NULL,
    phrase character varying(500) NOT NULL
);


ALTER TABLE public.trigger_phrases OWNER TO skillhub;

--
-- Name: users; Type: TABLE; Schema: public; Owner: skillhub
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    username character varying(100) NOT NULL,
    name character varying(255) NOT NULL,
    division character varying(100) NOT NULL,
    role character varying(100) NOT NULL,
    oauth_provider character varying(50),
    oauth_sub character varying(255),
    is_platform_team boolean NOT NULL,
    is_security_team boolean NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO skillhub;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (slug);


--
-- Name: comment_votes comment_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comment_votes
    ADD CONSTRAINT comment_votes_pkey PRIMARY KEY (comment_id, user_id);


--
-- Name: comments comments_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_pkey PRIMARY KEY (id);


--
-- Name: division_access_requests division_access_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.division_access_requests
    ADD CONSTRAINT division_access_requests_pkey PRIMARY KEY (id);


--
-- Name: divisions divisions_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.divisions
    ADD CONSTRAINT divisions_pkey PRIMARY KEY (slug);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (user_id, skill_id);


--
-- Name: feature_flags feature_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.feature_flags
    ADD CONSTRAINT feature_flags_pkey PRIMARY KEY (key);


--
-- Name: follows follows_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.follows
    ADD CONSTRAINT follows_pkey PRIMARY KEY (follower_id, followed_user_id);


--
-- Name: forks forks_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.forks
    ADD CONSTRAINT forks_pkey PRIMARY KEY (id);


--
-- Name: installs installs_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.installs
    ADD CONSTRAINT installs_pkey PRIMARY KEY (id);


--
-- Name: oauth_sessions oauth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.oauth_sessions
    ADD CONSTRAINT oauth_sessions_pkey PRIMARY KEY (id);


--
-- Name: replies replies_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.replies
    ADD CONSTRAINT replies_pkey PRIMARY KEY (id);


--
-- Name: review_votes review_votes_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_pkey PRIMARY KEY (review_id, user_id);


--
-- Name: reviews reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);


--
-- Name: skill_divisions skill_divisions_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_divisions
    ADD CONSTRAINT skill_divisions_pkey PRIMARY KEY (skill_id, division_slug);


--
-- Name: skill_tags skill_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_tags
    ADD CONSTRAINT skill_tags_pkey PRIMARY KEY (skill_id, tag);


--
-- Name: skill_versions skill_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT skill_versions_pkey PRIMARY KEY (id);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- Name: skills skills_slug_key; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_slug_key UNIQUE (slug);


--
-- Name: submission_gate_results submission_gate_results_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submission_gate_results
    ADD CONSTRAINT submission_gate_results_pkey PRIMARY KEY (id);


--
-- Name: submissions submissions_display_id_key; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_display_id_key UNIQUE (display_id);


--
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- Name: trigger_phrases trigger_phrases_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.trigger_phrases
    ADD CONSTRAINT trigger_phrases_pkey PRIMARY KEY (id);


--
-- Name: reviews uq_reviews_skill_user; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT uq_reviews_skill_user UNIQUE (skill_id, user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ix_audit_log_event_type; Type: INDEX; Schema: public; Owner: skillhub
--

CREATE INDEX ix_audit_log_event_type ON public.audit_log USING btree (event_type);


--
-- Name: ix_skill_versions_content_hash; Type: INDEX; Schema: public; Owner: skillhub
--

CREATE INDEX ix_skill_versions_content_hash ON public.skill_versions USING btree (content_hash);


--
-- Name: audit_log trg_audit_log_immutable; Type: TRIGGER; Schema: public; Owner: skillhub
--

CREATE TRIGGER trg_audit_log_immutable BEFORE DELETE OR UPDATE ON public.audit_log FOR EACH ROW EXECUTE FUNCTION public.audit_log_immutable();


--
-- Name: comment_votes comment_votes_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comment_votes
    ADD CONSTRAINT comment_votes_comment_id_fkey FOREIGN KEY (comment_id) REFERENCES public.comments(id) ON DELETE CASCADE;


--
-- Name: comment_votes comment_votes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comment_votes
    ADD CONSTRAINT comment_votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: comments comments_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: comments comments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: division_access_requests division_access_requests_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.division_access_requests
    ADD CONSTRAINT division_access_requests_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id);


--
-- Name: division_access_requests division_access_requests_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.division_access_requests
    ADD CONSTRAINT division_access_requests_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: favorites favorites_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: favorites favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: follows follows_followed_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.follows
    ADD CONSTRAINT follows_followed_user_id_fkey FOREIGN KEY (followed_user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: follows follows_follower_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.follows
    ADD CONSTRAINT follows_follower_id_fkey FOREIGN KEY (follower_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: forks forks_forked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.forks
    ADD CONSTRAINT forks_forked_by_fkey FOREIGN KEY (forked_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: forks forks_forked_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.forks
    ADD CONSTRAINT forks_forked_skill_id_fkey FOREIGN KEY (forked_skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: forks forks_original_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.forks
    ADD CONSTRAINT forks_original_skill_id_fkey FOREIGN KEY (original_skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: installs installs_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.installs
    ADD CONSTRAINT installs_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: installs installs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.installs
    ADD CONSTRAINT installs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: oauth_sessions oauth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.oauth_sessions
    ADD CONSTRAINT oauth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: replies replies_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.replies
    ADD CONSTRAINT replies_comment_id_fkey FOREIGN KEY (comment_id) REFERENCES public.comments(id) ON DELETE CASCADE;


--
-- Name: replies replies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.replies
    ADD CONSTRAINT replies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: review_votes review_votes_review_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.reviews(id) ON DELETE CASCADE;


--
-- Name: review_votes review_votes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.review_votes
    ADD CONSTRAINT review_votes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: reviews reviews_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: reviews reviews_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: skill_divisions skill_divisions_division_slug_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_divisions
    ADD CONSTRAINT skill_divisions_division_slug_fkey FOREIGN KEY (division_slug) REFERENCES public.divisions(slug);


--
-- Name: skill_divisions skill_divisions_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_divisions
    ADD CONSTRAINT skill_divisions_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_tags skill_tags_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_tags
    ADD CONSTRAINT skill_tags_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_versions skill_versions_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT skill_versions_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skills skills_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id);


--
-- Name: skills skills_category_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_category_fkey FOREIGN KEY (category) REFERENCES public.categories(slug);


--
-- Name: submission_gate_results submission_gate_results_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submission_gate_results
    ADD CONSTRAINT submission_gate_results_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.users(id);


--
-- Name: submission_gate_results submission_gate_results_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submission_gate_results
    ADD CONSTRAINT submission_gate_results_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: submissions submissions_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- Name: submissions submissions_submitted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_submitted_by_fkey FOREIGN KEY (submitted_by) REFERENCES public.users(id);


--
-- Name: trigger_phrases trigger_phrases_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.trigger_phrases
    ADD CONSTRAINT trigger_phrases_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: users users_division_fkey; Type: FK CONSTRAINT; Schema: public; Owner: skillhub
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_division_fkey FOREIGN KEY (division) REFERENCES public.divisions(slug);


--
-- PostgreSQL database dump complete
--

\unrestrict 9aCQnXqthQSb5EdIy05oZdpH1Mh3VVUqRz2yEoqbQ4UlGS6mnVzXaywQdx3Ui4P

